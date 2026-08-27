package com.northstar.underwriting.entity;

import java.math.BigDecimal;
import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Transient;

/**
 * Row in northstar.decisions.
 *
 * <p>reasonCodes is a comma separated string. It should be an array and Postgres supports
 * arrays. The column was created as TEXT in 2015 and three consumers split it on commas,
 * including one Excel export that Renee's team uses every Monday. So it stays TEXT.
 */
@Entity
@Table(name = "decisions", schema = "northstar")
public class DecisionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "decision_id")
    private Long decisionId;

    @Column(name = "application_id", nullable = false)
    private Long applicationId;

    @Column(name = "outcome", nullable = false)
    private String outcome;

    @Column(name = "reason_codes", length = 1024)
    private String reasonCodes;

    /**
     * The revenue number the decision was made with.
     *
     * <p>This is whatever RevenueCalculator returned at the time. There is no column saying
     * which definition of revenue that was, so old rows cannot be compared to new ones if
     * the definition ever changes.
     */
    @Column(name = "monthly_revenue_used", precision = 14, scale = 2)
    private BigDecimal monthlyRevenue;

    @Column(name = "dscr", precision = 8, scale = 4)
    private BigDecimal dscr;

    @Column(name = "decided_by")
    private String decidedBy;

    /** Not stored on decisions; carried on events and in-memory only. */
    @Transient
    private String tenantId;

    @Column(name = "created_at")
    private Instant createdAt;

    public Long getDecisionId() {
        return decisionId;
    }

    public void setDecisionId(Long decisionId) {
        this.decisionId = decisionId;
    }

    public Long getApplicationId() {
        return applicationId;
    }

    public void setApplicationId(Long applicationId) {
        this.applicationId = applicationId;
    }

    public String getOutcome() {
        return outcome;
    }

    public void setOutcome(String outcome) {
        this.outcome = outcome;
    }

    public String getReasonCodes() {
        return reasonCodes;
    }

    public void setReasonCodes(String reasonCodes) {
        this.reasonCodes = reasonCodes;
    }

    public BigDecimal getMonthlyRevenue() {
        return monthlyRevenue;
    }

    public void setMonthlyRevenue(BigDecimal monthlyRevenue) {
        this.monthlyRevenue = monthlyRevenue;
    }

    public BigDecimal getDscr() {
        return dscr;
    }

    public void setDscr(BigDecimal dscr) {
        this.dscr = dscr;
    }

    public String getDecidedBy() {
        return decidedBy;
    }

    public void setDecidedBy(String decidedBy) {
        this.decidedBy = decidedBy;
    }

    public String getTenantId() {
        return tenantId;
    }

    public void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }
}
