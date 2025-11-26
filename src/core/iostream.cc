/*
 * Copyright (C) 2025-present ScyllaDB
 */

/*
 * SPDX-License-Identifier: LicenseRef-ScyllaDB-Source-Available-1.0
 */

#include <seastar/core/iostream.hh>
#include <seastar/core/reactor.hh>

namespace seastar {
thread_local std::unordered_map<std::string, uint64_t> data_source::source_impl_types{};
thread_local std::unordered_map<std::string, uint64_t> data_sink::sink_impl_types{};

data_source_impl::data_source_impl() : _stats(io_stats::local()) {
    _stats.data_sources_count += 1;
}

data_source_impl::~data_source_impl() {
    _stats.data_sources_count -= 1;
}

data_source::data_source(std::unique_ptr<data_source_impl> dsi) noexcept : _dsi(std::move(dsi)) {
    const auto& type = *_dsi;
    _impl_name = pretty_type_name(typeid(type));
    if (_impl_name == "encryption::encrypted_data_source") {
        ++io_stats::local().encrypted_data_source;
    } else if (_impl_name == "seastar::http::experimental::skip_body_source") {
        ++io_stats::local().skip_body_source;
    } else if (_impl_name == "seastar::httpd::internal::chunked_source_impl") {
        ++io_stats::local().chunked_source_impl;
    } else if (_impl_name == "seastar::tls::tls_connected_socket_impl::source_impl") {
        ++io_stats::local().tls_connected_socket_source_impl;
    } else if (_impl_name == "seastar::httpd::internal::content_length_source_impl") {
        ++io_stats::local().content_length_source_impl;
    } else if (_impl_name == "s3::client::chunked_download_source") {
        ++io_stats::local().chunked_download_source;
    } else if (_impl_name == "compressed_file_data_source_impl<crc32_utils, true, (compressed_checksum_mode)1>") {
        ++io_stats::local().compressed_file_data_source_impl;
    } else if (_impl_name == "sstables::checksummed_file_data_source_impl<crc32_utils, true>") {
        ++io_stats::local().checksummed_file_data_source_impl;
    } else if (_impl_name == "generic_server::counted_data_source_impl") {
        ++io_stats::local().counted_data_source_impl;
    } else if (_impl_name == "seastar::net::posix_data_source_impl") {
        ++io_stats::local().posix_data_source_impl;
    } else if (_impl_name == "create_ranged_source(seastar::data_source, unsigned long, std::optional<unsigned long>)::ranged_data_source") {
        ++io_stats::local().ranged_data_source;
    } else if (_impl_name == "seastar::file_data_source_impl") {
        ++io_stats::local().file_data_source_impl;
    }
    source_impl_types[_impl_name]++;
}

data_source::~data_source() {
    if (_impl_name == "encryption::encrypted_data_source") {
        --io_stats::local().encrypted_data_source;
    } else if (_impl_name == "seastar::http::experimental::skip_body_source") {
        --io_stats::local().skip_body_source;
    } else if (_impl_name == "seastar::httpd::internal::chunked_source_impl") {
        --io_stats::local().chunked_source_impl;
    } else if (_impl_name == "seastar::tls::tls_connected_socket_impl::source_impl") {
        --io_stats::local().tls_connected_socket_source_impl;
    } else if (_impl_name == "seastar::httpd::internal::content_length_source_impl") {
        --io_stats::local().content_length_source_impl;
    } else if (_impl_name == "s3::client::chunked_download_source") {
        --io_stats::local().chunked_download_source;
    } else if (_impl_name == "compressed_file_data_source_impl<crc32_utils, true, (compressed_checksum_mode)1>") {
        --io_stats::local().compressed_file_data_source_impl;
    } else if (_impl_name == "sstables::checksummed_file_data_source_impl<crc32_utils, true>") {
        --io_stats::local().checksummed_file_data_source_impl;
    } else if (_impl_name == "generic_server::counted_data_source_impl") {
        --io_stats::local().counted_data_source_impl;
    } else if (_impl_name == "seastar::net::posix_data_source_impl") {
        --io_stats::local().posix_data_source_impl;
    } else if (_impl_name == "create_ranged_source(seastar::data_source, unsigned long, std::optional<unsigned long>)::ranged_data_source") {
        --io_stats::local().ranged_data_source;
    } else if (_impl_name == "seastar::file_data_source_impl") {
        --io_stats::local().file_data_source_impl;
    }
    source_impl_types[_impl_name]--;
}

data_sink_impl::data_sink_impl() : _stats(io_stats::local()) {
    _stats.data_sinks_count += 1;
}

data_sink_impl::~data_sink_impl() {
    _stats.data_sinks_count -= 1;
}

data_sink::data_sink(std::unique_ptr<data_sink_impl> dsi) noexcept : _dsi(std::move(dsi)) {
    const auto& type = *_dsi;
    _impl_name = pretty_type_name(typeid(type));
    if (_impl_name == "seastar::http::internal::http_content_length_data_sink_impl") {
        ++io_stats::local().http_content_length_data_sink_impl;
    } else if (_impl_name == "seastar::tls::tls_connected_socket_impl::sink_impl") {
        ++io_stats::local().tls_connected_socket_source_impl;
    } else if (_impl_name == "sstables::sizing_data_sink") {
        ++io_stats::local().sizing_data_sink;
    } else if (_impl_name == "compressed_file_data_sink_impl<crc32_utils, (compressed_checksum_mode)1>") {
        ++io_stats::local().compressed_file_data_sink_impl;
    } else if (_impl_name == "generic_server::counted_data_sink_impl") {
        ++io_stats::local().counted_data_sink_impl;
    } else if (_impl_name == "seastar::net::posix_data_sink_impl") {
        ++io_stats::local().posix_data_sink_impl;
    } else if (_impl_name == "sstables::checksummed_file_data_sink_impl<crc32_utils>") {
        ++io_stats::local().checksummed_file_data_sink_impl;
    } else if (_impl_name == "seastar::file_data_sink_impl") {
        ++io_stats::local().file_data_sink_impl;
    }
    sink_impl_types[_impl_name]++;
}

data_sink::~data_sink() {
    if (_impl_name == "seastar::http::internal::http_content_length_data_sink_impl") {
        --io_stats::local().http_content_length_data_sink_impl;
    } else if (_impl_name == "seastar::tls::tls_connected_socket_impl::sink_impl") {
        --io_stats::local().tls_connected_socket_source_impl;
    } else if (_impl_name == "sstables::sizing_data_sink") {
        --io_stats::local().sizing_data_sink;
    } else if (_impl_name == "compressed_file_data_sink_impl<crc32_utils, (compressed_checksum_mode)1>") {
        --io_stats::local().compressed_file_data_sink_impl;
    } else if (_impl_name == "generic_server::counted_data_sink_impl") {
        --io_stats::local().counted_data_sink_impl;
    } else if (_impl_name == "seastar::net::posix_data_sink_impl") {
        --io_stats::local().posix_data_sink_impl;
    } else if (_impl_name == "sstables::checksummed_file_data_sink_impl<crc32_utils>") {
        --io_stats::local().checksummed_file_data_sink_impl;
    } else if (_impl_name == "seastar::file_data_sink_impl") {
        --io_stats::local().file_data_sink_impl;
    }
    sink_impl_types[_impl_name]--;
}
} // namespace seastar
