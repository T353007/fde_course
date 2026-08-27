package com.northstar.application.repo;

import org.springframework.data.jpa.repository.JpaRepository;

import com.northstar.application.entity.ApplicationEntity;

public interface ApplicationRepository extends JpaRepository<ApplicationEntity, Long> {
}
