package com.northstar.common.dto;

import java.math.BigDecimal;
import java.util.Date;

/**
 * The main application read model. This is the oldest DTO in the platform.
 *
 * <p>The revenue field is always null. It was added in 2017 so the CRM sync could stop
 * making a second call to underwriting. The wiring was never finished. Nothing sets it and
 * two dashboards read it, which is why the CRM shows a blank revenue column for every
 * application. Support tells people to check the reviewer portal instead.
 *
 * <p>submittedAt is a java.util.Date because this class predates the Instant migration.
 * Everything written after 2021 uses Instant. Both are alive.
 */
public class ApplicationSummaryView {

    private Long applicationId;
    private Long applicantId;
    private String legalName;
    private String product;
    private String status;
    private BigDecimal amountRequested;

    /** Always null. See the class comment. Do not add it to a new caller. */
    private BigDecimal revenue;

    private Date submittedAt;
    private String tenantId;

    public ApplicationSummaryView() {
    }

    public Long getApplicationId() {
        return applicationId;
    }

    public void setApplicationId(Long applicationId) {
        this.applicationId = applicationId;
    }

    public Long getApplicantId() {
        return applicantId;
    }

    public void setApplicantId(Long applicantId) {
        this.applicantId = applicantId;
    }

    public String getLegalName() {
        return legalName;
    }

    public void setLegalName(String legalName) {
        this.legalName = legalName;
    }

    public String getProduct() {
        return product;
    }

    public void setProduct(String product) {
        this.product = product;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public BigDecimal getAmountRequested() {
        return amountRequested;
    }

    public void setAmountRequested(BigDecimal amountRequested) {
        this.amountRequested = amountRequested;
    }

    public BigDecimal getRevenue() {
        return revenue;
    }

    public void setRevenue(BigDecimal revenue) {
        this.revenue = revenue;
    }

    public Date getSubmittedAt() {
        return submittedAt;
    }

    public void setSubmittedAt(Date submittedAt) {
        this.submittedAt = submittedAt;
    }

    public String getTenantId() {
        return tenantId;
    }

    public void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }
}
