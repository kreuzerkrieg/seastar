/*
 * Copyright (C) 2025-present ScyllaDB
 */

/*
 * SPDX-License-Identifier: LicenseRef-ScyllaDB-Source-Available-1.0
 */

#pragma once
#include <seastar/core/future.hh>
#include <seastar/http/reply.hh>
#include <seastar/util/modules.hh>

namespace seastar {
SEASTAR_MODULE_EXPORT_BEGIN

namespace http::experimental {

class retry_strategy {
public:
    virtual ~retry_strategy() = default;
    // Just rethrow if the request should not be retried.
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
} // namespace http::experimental

SEASTAR_MODULE_EXPORT_END
} // namespace seastar
