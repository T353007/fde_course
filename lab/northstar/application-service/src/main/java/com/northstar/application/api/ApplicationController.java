package com.northstar.application.api;

import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.northstar.application.entity.ApplicationEntity;
import com.northstar.application.repo.ApplicationRepository;

/**
 * The portal API for a single application.
 *
 * <p>No tenant filter on the read. The id is treated as enough. That is how this looked in
 * 2014 and the reviewer portal still depends on being able to open a file after switching
 * brands.
 */
@RestController
@RequestMapping("/api/v1/applications")
public class ApplicationController {

    private final ApplicationRepository applicationRepository;

    public ApplicationController(ApplicationRepository applicationRepository) {
        this.applicationRepository = applicationRepository;
    }

    @GetMapping("/{applicationId}")
    public ResponseEntity<Map<String, Object>> get(@PathVariable Long applicationId) {
        return applicationRepository.findById(applicationId)
                .map(this::toBody)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    /**
     * Field names here are what the 2016 portal typed against. Keep the order.
     * revenue is not on this payload. It lives on ApplicationSummaryView, which is always
     * null. Two different reads, two different shapes.
     */
    private Map<String, Object> toBody(ApplicationEntity app) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("applicationId", app.getApplicationId());
        body.put("applicantId", app.getApplicantId());
        body.put("product", app.getProduct());
        body.put("amountRequested", scale(app.getAmountRequested()));
        body.put("status", app.getStatus());
        body.put("submittedAt", app.getSubmittedAt());
        body.put("decidedAt", app.getDecidedAt());
        body.put("customerId", app.getCustomerId());
        body.put("createdAt", app.getCreatedAt());
        body.put("updatedAt", app.getUpdatedAt());
        return body;
    }

    private static BigDecimal scale(BigDecimal value) {
        return value == null ? null : value.setScale(2, java.math.RoundingMode.HALF_UP);
    }
}
