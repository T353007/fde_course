package com.northstar.underwriting.api;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.northstar.common.model.BankTransaction;
import com.northstar.underwriting.entity.BankTransactionEntity;
import com.northstar.underwriting.repo.BankTransactionRepository;
import com.northstar.underwriting.revenue.RevenueCalculator;

/**
 * The URLs the reviewer portal and the curl tour actually hit.
 *
 * <p>Confluence documents monthlyRevenue. This payload uses avgMonthlyRevenue. revenue is
 * always null. calcVersion says v2 even though this path still calls RevenueCalculator,
 * the original one. The flag that would switch the decision engine never reached here.
 */
@RestController
@RequestMapping("/api/v1/applications")
public class ApplicationLookupController {

    private static final int DEFAULT_MONTHS = 3;

    private final BankTransactionRepository bankTransactionRepository;
    private final RevenueCalculator revenueCalculator;

    public ApplicationLookupController(BankTransactionRepository bankTransactionRepository,
                                       RevenueCalculator revenueCalculator) {
        this.bankTransactionRepository = bankTransactionRepository;
        this.revenueCalculator = revenueCalculator;
    }

    @GetMapping("/{applicationId}/revenue-summary")
    public ResponseEntity<Map<String, Object>> revenueSummary(@PathVariable Long applicationId) {
        List<BankTransactionEntity> rows =
                bankTransactionRepository.findByApplicationIdOrderByPostedDateAsc(applicationId);
        List<BankTransaction> transactions = rows.stream().map(BankTransactionEntity::toModel).toList();
        BigDecimal avg = revenueCalculator.calculateMonthlyRevenue(transactions, DEFAULT_MONTHS);

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("applicationId", applicationId);
        body.put("avgMonthlyRevenue", avg);
        body.put("revenue", null);
        body.put("monthsAnalyzed", DEFAULT_MONTHS);
        body.put("calculatedAt", Instant.now());
        body.put("calcVersion", "v2");
        return ResponseEntity.ok(body);
    }

    @GetMapping("/{applicationId}/bank-transactions")
    public ResponseEntity<Map<String, Object>> bankTransactions(@PathVariable Long applicationId) {
        List<Map<String, Object>> transactions = bankTransactionRepository
                .findByApplicationIdOrderByPostedDateAsc(applicationId)
                .stream()
                .map(row -> {
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("postedDate", row.getPostedDate());
                    item.put("description", row.getDescription());
                    item.put("amount", row.getAmount());
                    return item;
                })
                .toList();

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("applicationId", applicationId);
        body.put("transactions", transactions);
        return ResponseEntity.ok(body);
    }
}
