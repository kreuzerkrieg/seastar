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

/// Decides whether a connection survives a failed request attempt.
///
/// The client consults the policy on every failed attempt: a transport failure while
/// sending the request or reading the reply, a reply handler that failed, or a reply
/// with an unexpected status. The policy can only allow keeping the connection. One
/// that is already lost stays closed whatever the policy says: the server asked to
/// close it, the request was aborted, or the attempt failed with part of the reply
/// body unread.
///
/// When the policy allows keeping the connection and the request is retried, the retry
/// takes a pooled connection instead of a new one.
///
/// \see client::set_connection_reset_policy()
class connection_reset_policy {
public:
    virtual ~connection_reset_policy() = default;
    /// Tells whether the connection an attempt failed on must be closed.
    ///
    /// Called on the shard of the client, synchronously, so it must not block.
    ///
    /// \param error -- the exception the attempt failed with
    /// \return true to close the connection, false to allow keeping it
    [[nodiscard]] virtual bool should_reset(std::exception_ptr error) const = 0;
};

/// The client's default policy: closes every connection an attempt failed on.
class always_reset_policy final : public connection_reset_policy {
public:
    [[nodiscard]] bool should_reset(std::exception_ptr) const override {
        return true;
    }
};

} // namespace seastar::http
