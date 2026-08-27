package com.northstar.underwriting.entity;

import java.time.LocalDate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * Row in northstar.policy_documents.
 *
 * <p>effectiveFrom was added in migration V13 and is null on four of the eight rows.
 * Anything that filters on it drops those four, which includes credit-policy-FINAL.pdf.
 * Nothing warns you.
 */
@Entity
@Table(name = "policy_documents", schema = "northstar")
public class PolicyDocumentEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "policy_document_id")
    private Long policyDocumentId;

    @Column(name = "file_name", nullable = false)
    private String filename;

    @Column(name = "title")
    private String title;

    /** BASE, PRODUCT_OVERLAY, or TENANT_OVERLAY. Maps to doc_kind in the database. */
    @Column(name = "doc_kind")
    private String policyType;

    /** Null means "applies to every tenant". Also null means "we never filled it in". */
    @Column(name = "tenant_id")
    private String tenantId;

    @Column(name = "product")
    private String product;

    @Column(name = "effective_from")
    private LocalDate effectiveFrom;

    @Column(name = "storage_key")
    private String storageKey;

    public Long getPolicyDocumentId() {
        return policyDocumentId;
    }

    public void setPolicyDocumentId(Long policyDocumentId) {
        this.policyDocumentId = policyDocumentId;
    }

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getPolicyType() {
        return policyType;
    }

    public void setPolicyType(String policyType) {
        this.policyType = policyType;
    }

    public String getTenantId() {
        return tenantId;
    }

    public void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }

    public String getProduct() {
        return product;
    }

    public void setProduct(String product) {
        this.product = product;
    }

    public LocalDate getEffectiveFrom() {
        return effectiveFrom;
    }

    public void setEffectiveFrom(LocalDate effectiveFrom) {
        this.effectiveFrom = effectiveFrom;
    }

    public String getStorageKey() {
        return storageKey;
    }

    public void setStorageKey(String storageKey) {
        this.storageKey = storageKey;
    }
}
