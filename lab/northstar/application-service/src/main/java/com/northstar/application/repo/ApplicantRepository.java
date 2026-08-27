package com.northstar.application.repo;

import org.springframework.data.jpa.repository.JpaRepository;

import com.northstar.application.entity.ApplicantEntity;

public interface ApplicantRepository extends JpaRepository<ApplicantEntity, Long> {
}
