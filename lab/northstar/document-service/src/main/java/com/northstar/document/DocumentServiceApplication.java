package com.northstar.document;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;

import com.northstar.common.tenant.TenantHeaderFilter;

@SpringBootApplication
public class DocumentServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(DocumentServiceApplication.class, args);
    }

    /** Header convention only. No customer_id support in this service. */
    @Bean
    public FilterRegistrationBean<TenantHeaderFilter> tenantHeaderFilter() {
        FilterRegistrationBean<TenantHeaderFilter> registration = new FilterRegistrationBean<>();
        registration.setFilter(new TenantHeaderFilter());
        registration.addUrlPatterns("/api/*");
        registration.setOrder(10);
        return registration;
    }
}
