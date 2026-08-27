package com.northstar.underwriting.repo;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.northstar.underwriting.entity.DecisionEntity;

public interface DecisionRepository extends JpaRepository<DecisionEntity, Long> {

    List<DecisionEntity> findByApplicationIdOrderByCreatedAtDesc(Long applicationId);

    Optional<DecisionEntity> findFirstByApplicationIdOrderByCreatedAtDesc(Long applicationId);
}
