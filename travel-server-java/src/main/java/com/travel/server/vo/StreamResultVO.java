package com.travel.server.vo;

/**
 * SSE 流式规划结果事件
 */
public class StreamResultVO {

    private String type;
    private TravelRecommendVO data;

    public StreamResultVO() {}

    public StreamResultVO(TravelRecommendVO data) {
        this.type = "result";
        this.data = data;
    }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    public TravelRecommendVO getData() { return data; }
    public void setData(TravelRecommendVO data) { this.data = data; }
}
