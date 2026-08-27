package com.northstar.application.entity;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * Row in northstar.applicants.
 *
 * <p>ein is nullable and there is no unique index on it. The portal does not validate the
 * format either, so the same business shows up with 56-1234567, 561234567, and 56 1234567.
 * Sales called that a feature in 2016 because it kept the form short.
 */
@Entity
@Table(name = "applicants", schema = "northstar")
public class ApplicantEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "applicant_id")
    private Long applicantId;

    @Column(name = "legal_name", nullable = false)
    private String legalName;

    @Column(name = "dba_name")
    private String dbaName;

    /** Nullable, not unique, and often wrong. */
    @Column(name = "ein")
    private String ein;

    @Column(name = "owner_ssn_last4", length = 4)
    private String ownerSsnLast4;

    @Column(name = "email")
    private String email;

    @Column(name = "phone")
    private String phone;

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @Column(name = "created_at")
    private Instant createdAt;

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

    public String getDbaName() {
        return dbaName;
    }

    public void setDbaName(String dbaName) {
        this.dbaName = dbaName;
    }

    public String getEin() {
        return ein;
    }

    public void setEin(String ein) {
        this.ein = ein;
    }

    public String getOwnerSsnLast4() {
        return ownerSsnLast4;
    }

    public void setOwnerSsnLast4(String ownerSsnLast4) {
        this.ownerSsnLast4 = ownerSsnLast4;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
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
