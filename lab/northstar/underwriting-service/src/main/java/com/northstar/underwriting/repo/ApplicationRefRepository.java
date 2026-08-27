package com.northstar.underwriting.repo;

import org.springframework.data.jpa.repository.JpaRepository;

import com.northstar.underwriting.entity.ApplicationRefEntity;

/** Read only access to a table this service does not own. See the entity comment. */
public interface ApplicationRefRepository extends JpaRepository<ApplicationRefEntity, Long> {
}
