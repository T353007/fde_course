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
 * The 2015 convention. Reads the customer_id request parameter.
 *
 * <p>Only application-service installs this one. It also checks the header, because a
 * 2023 patch added header support without removing the param support. So this service
 * accepts both and the other three services accept one. That difference is why a request
 * that works against the portal API can silently pick a different tenant when it is
 * replayed against underwriting.
 */
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class LegacyCustomerIdTenantFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        try {
            if (request instanceof HttpServletRequest http) {
                // 2023 patch. Header first, then fall back to the old param.
                String tenant = TenantResolver.resolve(http);
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
