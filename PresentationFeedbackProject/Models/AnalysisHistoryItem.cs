using System;

namespace PresentationFeedbackUI.Models
{
    public class AnalysisHistoryItem
    {
        public int Id { get; set; }
        public int UserId { get; set; }
        public string VideoPath { get; set; } = "";
        public string VideoName { get; set; } = "";
        public DateTime CreatedAt { get; set; }
        public AnalysisResult Result { get; set; } = new AnalysisResult();

        public string SummaryText => $"{CreatedAt:yyyy-MM-dd HH:mm}  ·  {Result.TotalScore}점  ·  {VideoName}";
    }
}
