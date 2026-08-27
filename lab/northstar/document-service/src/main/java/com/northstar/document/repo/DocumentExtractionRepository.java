package com.northstar.document.repo;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.northstar.document.entity.DocumentExtractionEntity;

public interface DocumentExtractionRepository extends JpaRepository<DocumentExtractionEntity, Long> {

    List<DocumentExtractionEntity> findByDocumentIdOrderByExtractedAtDesc(Long documentId);
}
