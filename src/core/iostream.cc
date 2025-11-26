/*
 * Copyright (C) 2025-present ScyllaDB
 */

/*
 * SPDX-License-Identifier: LicenseRef-ScyllaDB-Source-Available-1.0
 */

#include <seastar/core/reactor.hh>

namespace seastar {
data_source_impl::data_source_impl() : _stats(io_stats::local()) {
    _stats.data_sources_count += 1;
}
data_source_impl::~data_source_impl() {
    _stats.data_sources_count -= 1;
}

data_sink_impl::data_sink_impl() : _stats(io_stats::local()) {
    _stats.data_sinks_count += 1;
}
data_sink_impl::~data_sink_impl() {
    _stats.data_sinks_count -= 1;
}
}