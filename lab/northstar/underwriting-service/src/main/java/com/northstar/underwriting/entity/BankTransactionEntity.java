package com.northstar.underwriting.entity;

import java.math.BigDecimal;
import java.time.LocalDate;

import com.northstar.common.model.BankTransaction;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Transient;

/** Row in northstar.bank_transactions. */
@Entity
@Table(name = "bank_transactions", schema = "northstar")
public class BankTransactionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "transaction_id")
    private Long bankTransactionId;

    @Column(name = "application_id", nullable = false)
    private Long applicationId;

    @Column(name = "document_id")
    private Long documentId;

    @Column(name = "posted_date")
    private LocalDate postedDate;

    @Column(name = "description", length = 512)
    private String description;

    @Column(name = "amount", precision = 14, scale = 2)
    private BigDecimal amount;

    /** Null on most rows before 2024. */
    @Column(name = "category")
    private String category;

    /** Added in V12. Null on everything loaded before that migration. */
    @Column(name = "category_source")
    private String categorySource;

    /** Not stored on bank_transactions; kept for Kafka ingest and tenant-scoped queries. */
    @Transient
    private String tenantId;

    public BankTransaction toModel() {
        return new BankTransaction(bankTransactionId, applicationId, postedDate, description, amount,
                category, categorySource);
    }

    public Long getBankTransactionId() {
        return bankTransactionId;
    }

    public void setBankTransactionId(Long bankTransactionId) {
        this.bankTransactionId = bankTransactionId;
    }

    public Long getApplicationId() {
        return applicationId;
    }

    public void setApplicationId(Long applicationId) {
        this.applicationId = applicationId;
    }

    public Long getDocumentId() {
        return documentId;
    }

    public void setDocumentId(Long documentId) {
        this.documentId = documentId;
    }

    public LocalDate getPostedDate() {
        return postedDate;
    }

    public void setPostedDate(LocalDate postedDate) {
        this.postedDate = postedDate;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public String getCategorySource() {
        return categorySource;
    }

    public void setCategorySource(String categorySource) {
        this.categorySource = categorySource;
    }

    public String getTenantId() {
        return tenantId;
    }

    public void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }
}
