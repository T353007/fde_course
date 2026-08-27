package com.northstar.underwriting.config;

import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.northstar.common.tenant.TenantHeaderFilter;

/** Installs the 2019 tenant convention. Header only. No customer_id support here. */
@Configuration
public class WebConfig {

    @Bean
    public FilterRegistrationBean<TenantHeaderFilter> tenantHeaderFilter() {
        FilterRegistrationBean<TenantHeaderFilter> registration = new FilterRegistrationBean<>();
        registration.setFilter(new TenantHeaderFilter());
        registration.addUrlPatterns("/api/*");
        registration.setOrder(10);
        return registration;
    }
}
