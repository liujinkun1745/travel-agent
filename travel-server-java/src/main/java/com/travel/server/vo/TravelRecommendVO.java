package com.travel.server.vo;

import java.util.List;

/**
 * 旅游推荐响应
 */
public class TravelRecommendVO {

    private Boolean success;
    private String city;
    private Integer days;
    private Integer totalBudget;
    private List<DailyItinerary> dailyItinerary;
    private BudgetBreakdown budgetBreakdown;
    private List<String> tips;
    private List<String> warnings;
    private String sessionId;
    private String error;
    private String rawResponse;

    public Boolean getSuccess() { return success; }
    public void setSuccess(Boolean success) { this.success = success; }
    public String getCity() { return city; }
    public void setCity(String city) { this.city = city; }
    public Integer getDays() { return days; }
    public void setDays(Integer days) { this.days = days; }
    public Integer getTotalBudget() { return totalBudget; }
    public void setTotalBudget(Integer totalBudget) { this.totalBudget = totalBudget; }
    public List<DailyItinerary> getDailyItinerary() { return dailyItinerary; }
    public void setDailyItinerary(List<DailyItinerary> dailyItinerary) { this.dailyItinerary = dailyItinerary; }
    public BudgetBreakdown getBudgetBreakdown() { return budgetBreakdown; }
    public void setBudgetBreakdown(BudgetBreakdown budgetBreakdown) { this.budgetBreakdown = budgetBreakdown; }
    public List<String> getTips() { return tips; }
    public void setTips(List<String> tips) { this.tips = tips; }
    public List<String> getWarnings() { return warnings; }
    public void setWarnings(List<String> warnings) { this.warnings = warnings; }
    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    public String getError() { return error; }
    public void setError(String error) { this.error = error; }
    public String getRawResponse() { return rawResponse; }
    public void setRawResponse(String rawResponse) { this.rawResponse = rawResponse; }

    /**
     * 每日行程
     */
    public static class DailyItinerary {
        private Integer day;
        private String date;
        private TimeSlot morning;
        private TimeSlot afternoon;
        private TimeSlot evening;

        public Integer getDay() { return day; }
        public void setDay(Integer day) { this.day = day; }
        public String getDate() { return date; }
        public void setDate(String date) { this.date = date; }
        public TimeSlot getMorning() { return morning; }
        public void setMorning(TimeSlot morning) { this.morning = morning; }
        public TimeSlot getAfternoon() { return afternoon; }
        public void setAfternoon(TimeSlot afternoon) { this.afternoon = afternoon; }
        public TimeSlot getEvening() { return evening; }
        public void setEvening(TimeSlot evening) { this.evening = evening; }
    }

    /**
     * 时间段（上午/下午/晚上）
     */
    public static class TimeSlot {
        private String spot;
        private String duration;
        private String ticket;
        private String transportation;
        private String description;

        public String getSpot() { return spot; }
        public void setSpot(String spot) { this.spot = spot; }
        public String getDuration() { return duration; }
        public void setDuration(String duration) { this.duration = duration; }
        public String getTicket() { return ticket; }
        public void setTicket(String ticket) { this.ticket = ticket; }
        public String getTransportation() { return transportation; }
        public void setTransportation(String transportation) { this.transportation = transportation; }
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
    }

    /**
     * 预算明细
     */
    public static class BudgetBreakdown {
        private Integer accommodation;
        private Integer food;
        private Integer transportation;
        private Integer tickets;
        private Integer other;

        public Integer getAccommodation() { return accommodation; }
        public void setAccommodation(Integer accommodation) { this.accommodation = accommodation; }
        public Integer getFood() { return food; }
        public void setFood(Integer food) { this.food = food; }
        public Integer getTransportation() { return transportation; }
        public void setTransportation(Integer transportation) { this.transportation = transportation; }
        public Integer getTickets() { return tickets; }
        public void setTickets(Integer tickets) { this.tickets = tickets; }
        public Integer getOther() { return other; }
        public void setOther(Integer other) { this.other = other; }
    }
}
