namespace PresentationFeedbackUI.Models
{
    public class AnalysisResult
    {
        public int TotalScore { get; set; }

        public int SpeechRateScore { get; set; }
        public int EyeContactScore { get; set; }
        public int GestureScore { get; set; }
        public int SilenceScore { get; set; }
        public int ContentScore { get; set; }

        public int Wpm { get; set; }

        public string Grade { get; set; } = "";

        public string OverallFeedback { get; set; } = "";
        public string SpeedFeedback { get; set; } = "";
        public string EyeContactFeedback { get; set; } = "";
        public string GestureFeedback { get; set; } = "";
        public string SilenceFeedback { get; set; } = "";
        public string ContentFeedback { get; set; } = "";
        public string Transcript { get; set; } = "";

        public string PresentationTopic { get; set; } = "";
        public string MainKeywords { get; set; } = "";
        public string ContentImprovement { get; set; } = "";
    }
}
