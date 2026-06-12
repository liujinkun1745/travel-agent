package com.travel.server.dto;

import jakarta.validation.constraints.*;

/**
 * 旅游规划请求
 */
public class TravelRequestDTO {

    @NotBlank(message = "城市不能为空")
    private String city;

    @NotNull(message = "预算不能为空")
    @DecimalMin(value = "100", message = "预算不能低于100元")
    @DecimalMax(value = "1000000", message = "预算不能超过100万元")
    private Double budget;

    @NotNull(message = "天数不能为空")
    @Min(value = 1, message = "天数至少为1天")
    @Max(value = 30, message = "天数不能超过30天")
    private Integer days;

    public TravelRequestDTO() {}

    public TravelRequestDTO(String city, Double budget, Integer days) {
        this.city = city;
        this.budget = budget;
        this.days = days;
    }

    public String getCity() { return city; }
    public void setCity(String city) { this.city = city; }
    public Double getBudget() { return budget; }
    public void setBudget(Double budget) { this.budget = budget; }
    public Integer getDays() { return days; }
    public void setDays(Integer days) { this.days = days; }
}
