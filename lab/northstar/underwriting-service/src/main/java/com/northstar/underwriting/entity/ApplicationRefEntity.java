package com.northstar.underwriting.entity;

import java.math.BigDecimal;
import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * northstar.applications, mapped read only from this service.
 *
 * <p>application-service owns this table. Underwriting reads it directly instead of calling
 * the API, because in 2017 the API was slow and the deadline was real. Nobody has removed
 * the direct read. It means a column change in application-service can break underwriting
 * at runtime with no compile error anywhere.
 *
 * <p>Do not write to this entity. There are no setters for status on purpose.
 */
@Entity
@Table(name = "applications", schema = "northstar")
public class ApplicationRefEntity {

    @Id
    @Column(name = "application_id")
    private Long applicationId;

    @Column(name = "applicant_id")
    private Long applicantId;

    @Column(name = "product")
    private String product;

    @Column(name = "amount_requested", precision = 14, scale = 2)
    private BigDecimal amountRequested;

    @Column(name = "status")
    private String status;

    /** Client supplied. See the note in application-service. Not the same as the event time. */
    @Column(name = "submitted_at")
    private Instant submittedAt;

    /** The second tenant convention lives in this column. */
    @Column(name = "customer_id")
    private String customerId;

    public Long getApplicationId() {
        return applicationId;
    }

    public Long getApplicantId() {
        return applicantId;
    }

    public String getProduct() {
        return product;
    }

    public BigDecimal getAmountRequested() {
        return amountRequested;
    }

    public String getStatus() {
        return status;
    }

    public Instant getSubmittedAt() {
        return submittedAt;
    }

    public String getCustomerId() {
        return customerId;
    }
}
