/*
 * Copyright (C) 2025-present ScyllaDB
 */

/*
 * SPDX-License-Identifier: LicenseRef-ScyllaDB-Source-Available-1.0
 */

#pragma once
#include <seastar/core/future.hh>
#include <seastar/http/reply.hh>

namespace seastar::http {

class retry_strategy {
public:
    virtual ~retry_strategy() = default;
    // Returns true if the error can be retried given the error and the number of times already tried.
    virtual future<bool> should_retry(std::exception_ptr error, unsigned attempted_retries) const = 0;
};

class default_retry_strategy final : public retry_strategy {
    unsigned _max_retries;

public:
    default_retry_strategy();
    explicit default_retry_strategy(unsigned max_retries);

    future<bool> should_retry(std::exception_ptr error, unsigned attempted_retries) const override;
};

class no_retry_strategy final : public retry_strategy {
public:
    future<bool> should_retry(std::exception_ptr error, unsigned attempted_retries) const override;
};

/// Decides whether a connection survives a reply handler that failed.
///
/// The client consults the policy only when a whole reply head arrived and the reply
/// handler (or the check of the expected status) then failed. A failure before the
/// reply head always closes the connection. The policy can only allow keeping the
/// connection: the client keeps it only when the reply body was also consumed, or is
/// short enough to drain, so a connection whose framing is lost is closed whatever the
/// policy says.
///
/// When the connection is kept and the request is retried, the retry goes over a pooled
/// connection instead of a new one.
///
/// \see client::set_connection_reset_policy()
class connection_reset_policy {
public:
    virtual ~connection_reset_policy() = default;
    /// Tells whether the connection the reply handler failed on must be closed.
    ///
    /// Called on the shard of the client, synchronously, so it must not block.
    ///
    /// \param error -- the exception the reply handler failed with
    /// \return true to close the connection, false to allow keeping it
    [[nodiscard]] virtual bool should_reset(std::exception_ptr error) const = 0;
};

/// The client's default policy: closes every connection a reply handler failed on.
class always_reset_policy final : public connection_reset_policy {
public:
    [[nodiscard]] bool should_reset(std::exception_ptr) const override {
        return true;
    }
};

} // namespace seastar::http
