package com.northstar.underwriting.repo;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.northstar.underwriting.entity.BankTransactionEntity;

public interface BankTransactionRepository extends JpaRepository<BankTransactionEntity, Long> {

    List<BankTransactionEntity> findByApplicationIdOrderByPostedDateAsc(Long applicationId);

    /**
     * Counts how many months of statement history we have for an application.
     *
     * <p>Counts distinct year and month pairs. If an applicant uploads two statements for
     * the same month, this returns 1, which is right. If they upload a statement that spans
     * a month boundary, this returns 2, which is arguable.
     */
    @Query("""
           select count(distinct function('to_char', t.postedDate, 'YYYY-MM'))
           from BankTransactionEntity t
           where t.applicationId = :applicationId
           """)
    Long countMonthsOfHistory(@Param("applicationId") Long applicationId);
}
