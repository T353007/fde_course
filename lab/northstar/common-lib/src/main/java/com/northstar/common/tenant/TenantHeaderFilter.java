package com.northstar.common.tenant;

import java.io.IOException;

import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;

/**
 * The 2019 convention. Reads X-Tenant-Id and nothing else.
 *
 * <p>Used by underwriting-service, document-service, and fraud-service. If the header is
 * missing the request still runs, with the default tenant. There was an attempt in 2022 to
 * reject those requests with a 400. It broke the nightly CRM sync, which sends no header,
 * and was reverted the same day.
 */
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class TenantHeaderFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        try {
            if (request instanceof HttpServletRequest http) {
                String tenant = TenantResolver.fromHeader(http);
                if (tenant != null) {
                    TenantContext.set(tenant);
                }
            }
            chain.doFilter(request, response);
        } finally {
            TenantContext.clear();
        }
    }
}
