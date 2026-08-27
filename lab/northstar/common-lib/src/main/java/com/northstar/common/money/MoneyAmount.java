package com.northstar.common.money;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * A money type from the 2018 "stop passing BigDecimal around" effort.
 *
 * <p>The effort covered common-lib and about a third of underwriting-service, then the
 * person driving it moved to the data team. Converting the rest would touch every
 * repository and every DTO, so it stopped. Two call sites still use this class. Everything
 * else uses plain BigDecimal.
 *
 * <p>Do not start using it in new code. Do not delete it either, the SBA limit table reads
 * it.
 *
 * @deprecated the refactor that needed this was abandoned in 2018. Use BigDecimal.
 */
@Deprecated(since = "2018-11")
public final class MoneyAmount implements Comparable<MoneyAmount> {

    public static final MoneyAmount ZERO = new MoneyAmount(BigDecimal.ZERO);

    private final BigDecimal value;

    private MoneyAmount(BigDecimal value) {
        this.value = value.setScale(2, RoundingMode.HALF_UP);
    }

    public static MoneyAmount of(BigDecimal value) {
        return value == null ? ZERO : new MoneyAmount(value);
    }

    public static MoneyAmount of(String value) {
        return new MoneyAmount(new BigDecimal(value));
    }

    public BigDecimal toBigDecimal() {
        return value;
    }

    public MoneyAmount plus(MoneyAmount other) {
        return new MoneyAmount(value.add(other.value));
    }

    public boolean isGreaterThan(MoneyAmount other) {
        return value.compareTo(other.value) > 0;
    }

    @Override
    public int compareTo(MoneyAmount other) {
        return value.compareTo(other.value);
    }

    @Override
    public boolean equals(Object o) {
        return o instanceof MoneyAmount m && value.compareTo(m.value) == 0;
    }

    @Override
    public int hashCode() {
        return value.stripTrailingZeros().hashCode();
    }

    @Override
    public String toString() {
        return value.toPlainString();
    }
}
