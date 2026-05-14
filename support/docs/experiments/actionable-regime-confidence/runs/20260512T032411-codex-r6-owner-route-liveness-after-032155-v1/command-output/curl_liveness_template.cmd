curl -L -sS -o /dev/null -D <headers> -w http_code=%{http_code},url_effective=%{url_effective},content_type=%{content_type},size_download=%{size_download},time_total=%{time_total} <url>
