package com.northstar.underwriting.api;

import java.math.BigDecimal;
import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.northstar.common.dto.UnderwritingRevenueView;
import com.northstar.common.model.BankTransaction;
import com.northstar.underwriting.entity.BankTransactionEntity;
import com.northstar.underwriting.repo.BankTransactionRepository;
import com.northstar.underwriting.revenue.RevenueCalculator;

/**
 * Revenue endpoints.
 *
 * <p>This controller does the work itself instead of calling a service. That is how the
 * whole service looked in 2017. Most of it has been moved out since. This one stayed
 * because it is two lines of logic and nobody wanted to touch a path the portal depends on.
 *
 * <p>Note what is not here: the USE_NEW_REVENUE_CALC_V2_TEMP check. The flag was added to
 * the two decision services in 2021 and this call site was not part of that change. If
 * anyone ever turns the flag on, the decision engine and this endpoint will report two
 * different revenue numbers for the same application.
 */
@RestController
@RequestMapping("/api/v1/underwriting")
public class RevenueController {

    private static final int DEFAULT_MONTHS = 3;

    private final BankTransactionRepository bankTransactionRepository;
    private final RevenueCalculator revenueCalculator;

    public RevenueController(BankTransactionRepository bankTransactionRepository,
                             RevenueCalculator revenueCalculator) {
        this.bankTransactionRepository = bankTransactionRepository;
        this.revenueCalculator = revenueCalculator;
    }

    /**
     * Average monthly revenue for an application.
     *
     * <p>application-service calls this for the applicant facing cash flow widget. The
     * reviewer portal also calls it. So does one Looker dashboard through a proxy.
     */
    @GetMapping("/applications/{applicationId}/revenue")
    public ResponseEntity<UnderwritingRevenueView> getRevenue(
            @PathVariable Long applicationId,
            @RequestParam(name = "months", required = false) Integer months) {

        List<BankTransactionEntity> rows =
                bankTransactionRepository.findByApplicationIdOrderByPostedDateAsc(applicationId);

        if (rows.isEmpty()) {
            // Returns zero, not 404. The portal widget renders 404 as a red error box and
            // support got tired of explaining it. Changed in 2020.
            return ResponseEntity.ok(new UnderwritingRevenueView(
                    applicationId, BigDecimal.ZERO, 0, "TOTAL_CREDITS"));
        }

        int monthsToUse = months != null && months > 0 ? months : DEFAULT_MONTHS;
        List<BankTransaction> transactions = rows.stream().map(BankTransactionEntity::toModel).toList();

        BigDecimal monthlyRevenue = revenueCalculator.calculateMonthlyRevenue(transactions, monthsToUse);

        // basis is hardcoded and it happens to be accurate today. If the calculator ever
        // changes, this string will not.
        return ResponseEntity.ok(new UnderwritingRevenueView(
                applicationId, monthlyRevenue, monthsToUse, "TOTAL_CREDITS"));
    }
}
