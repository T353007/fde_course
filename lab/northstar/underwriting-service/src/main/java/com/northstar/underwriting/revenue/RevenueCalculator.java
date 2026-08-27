package com.northstar.underwriting.revenue;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

import org.springframework.stereotype.Component;

import com.northstar.common.model.BankTransaction;

@Component
public class RevenueCalculator {

    /**
     * Calculates average monthly revenue from bank transactions.
     *
     * TODO(jkowalski, 2019-08): this counts every credit. Underwriting says
     * transfers and loan deposits should not count. Waiting on a decision
     * from credit policy before changing it. Do not change without asking
     * Renee, three other things depend on this number.
     */
    public BigDecimal calculateMonthlyRevenue(List<BankTransaction> transactions,
                                              int months) {
        BigDecimal total = BigDecimal.ZERO;

        for (BankTransaction t : transactions) {
            if (t.amount().signum() > 0) {
                total = total.add(t.amount());
            }
        }

        if (months <= 0) {
            return BigDecimal.ZERO;
        }

        return total.divide(BigDecimal.valueOf(months), 2, RoundingMode.HALF_UP);
    }
}
