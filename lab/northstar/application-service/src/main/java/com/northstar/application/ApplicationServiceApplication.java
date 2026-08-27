package com.northstar.application;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;

import com.northstar.common.tenant.LegacyCustomerIdTenantFilter;

@SpringBootApplication
public class ApplicationServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(ApplicationServiceApplication.class, args);
    }

    /**
     * The 2015 convention. Header is also accepted, because a 2023 patch added it without
     * removing the param. The other three services only read the header.
     */
    @Bean
    public FilterRegistrationBean<LegacyCustomerIdTenantFilter> legacyCustomerIdTenantFilter() {
        FilterRegistrationBean<LegacyCustomerIdTenantFilter> registration = new FilterRegistrationBean<>();
        registration.setFilter(new LegacyCustomerIdTenantFilter());
        registration.addUrlPatterns("/api/*", "/v1/*");
        registration.setOrder(10);
        return registration;
    }
}
