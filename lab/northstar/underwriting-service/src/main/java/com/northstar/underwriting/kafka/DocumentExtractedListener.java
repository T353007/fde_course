package com.northstar.underwriting.kafka;

import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.northstar.common.event.DocumentExtractedEvent;
import com.northstar.common.model.BankTransaction;
import com.northstar.underwriting.entity.BankTransactionEntity;
import com.northstar.underwriting.repo.BankTransactionRepository;

/**
 * Consumes document.extracted and stores the transactions.
 *
 * <p>Writes rows with category null and category_source null. The classification step that
 * was supposed to fill those in never shipped, which is why most of bank_transactions has
 * no category.
 */
@Component
public class DocumentExtractedListener {

    private static final Logger log = LoggerFactory.getLogger(DocumentExtractedListener.class);

    private final BankTransactionRepository repository;

    public DocumentExtractedListener(BankTransactionRepository repository) {
        this.repository = repository;
    }

    @KafkaListener(topics = "document.extracted", groupId = "underwriting-service")
    @Transactional
    public void onDocumentExtracted(DocumentExtractedEvent event) {
        if (event.transactions() == null || event.transactions().isEmpty()) {
            log.info("document.extracted had no transactions documentId={}", event.documentId());
            return;
        }

        List<BankTransactionEntity> rows = new ArrayList<>();
        for (BankTransaction txn : event.transactions()) {
            BankTransactionEntity row = new BankTransactionEntity();
            row.setApplicationId(event.applicationId());
            row.setDocumentId(event.documentId());
            row.setPostedDate(txn.postedDate());
            row.setDescription(txn.description());
            row.setAmount(txn.amount());
            row.setCategory(txn.category());
            row.setCategorySource(txn.categorySource());
            row.setTenantId(event.tenantId());
            rows.add(row);
        }

        repository.saveAll(rows);
        log.info("stored {} bank transactions for application {}", rows.size(), event.applicationId());
    }
}
