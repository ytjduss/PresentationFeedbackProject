using System.ComponentModel;
using System.Runtime.CompilerServices;
using PresentationFeedbackUI.Models;

namespace PresentationFeedbackUI.ViewModels
{
    public class AnalysisViewModel : INotifyPropertyChanged
    {
        private AnalysisResult result = new AnalysisResult();

        public event PropertyChangedEventHandler? PropertyChanged;

        public int TotalScore => result.TotalScore;

        public int SpeechRateScore => result.SpeechRateScore;
        public int EyeContactScore => result.EyeContactScore;
        public int GestureScore => result.GestureScore;
        public int SilenceScore => result.SilenceScore;
        public int ContentScore => result.ContentScore;

        public int Wpm => result.Wpm;

        public string Grade => string.IsNullOrWhiteSpace(result.Grade)
            ? "평가 없음"
            : result.Grade;
        public string GradeBadgeText => $"★ {Grade}";

        public string TotalScoreText => $"{TotalScore}";
        public string SpeechRateScoreText => $"{SpeechRateScore} /100";
        public string EyeContactScoreText => $"{EyeContactScore} /100";
        public string GestureScoreText => $"{GestureScore} /100";
        public string SilenceScoreText => $"{SilenceScore} /100";
        public string ContentScoreText => $"{ContentScore} /100";
        public string WpmText => $"{Wpm} WPM";

        public string OverallFeedback => result.OverallFeedback;
        public string SpeedFeedback => result.SpeedFeedback;
        public string EyeContactFeedback => result.EyeContactFeedback;
        public string GestureFeedback => result.GestureFeedback;
        public string SilenceFeedback => result.SilenceFeedback;
        public string ContentFeedback => result.ContentFeedback;
        public string Transcript => string.IsNullOrWhiteSpace(result.Transcript)
            ? "분석된 발표 대본이 없습니다."
            : result.Transcript;

        public string PresentationTopic => result.PresentationTopic;
        public string MainKeywords => result.MainKeywords;
        public string ContentImprovement => result.ContentImprovement;

        public double SpeechRateBarWidth => SpeechRateScore * 2.6;
        public double EyeContactBarWidth => EyeContactScore * 2.6;
        public double GestureBarWidth => GestureScore * 2.6;
        public double SilenceBarWidth => SilenceScore * 2.6;
        public double ContentBarWidth => ContentScore * 2.6;

        public void SetResult(AnalysisResult newResult)
        {
            result = newResult;

            OnPropertyChanged(nameof(TotalScore));
            OnPropertyChanged(nameof(SpeechRateScore));
            OnPropertyChanged(nameof(EyeContactScore));
            OnPropertyChanged(nameof(GestureScore));
            OnPropertyChanged(nameof(SilenceScore));
            OnPropertyChanged(nameof(ContentScore));
            OnPropertyChanged(nameof(Wpm));
            OnPropertyChanged(nameof(Grade));
            OnPropertyChanged(nameof(GradeBadgeText));

            OnPropertyChanged(nameof(TotalScoreText));
            OnPropertyChanged(nameof(SpeechRateScoreText));
            OnPropertyChanged(nameof(EyeContactScoreText));
            OnPropertyChanged(nameof(GestureScoreText));
            OnPropertyChanged(nameof(SilenceScoreText));
            OnPropertyChanged(nameof(ContentScoreText));
            OnPropertyChanged(nameof(WpmText));

            OnPropertyChanged(nameof(OverallFeedback));
            OnPropertyChanged(nameof(SpeedFeedback));
            OnPropertyChanged(nameof(EyeContactFeedback));
            OnPropertyChanged(nameof(GestureFeedback));
            OnPropertyChanged(nameof(SilenceFeedback));
            OnPropertyChanged(nameof(ContentFeedback));
            OnPropertyChanged(nameof(Transcript));

            OnPropertyChanged(nameof(PresentationTopic));
            OnPropertyChanged(nameof(MainKeywords));
            OnPropertyChanged(nameof(ContentImprovement));

            OnPropertyChanged(nameof(SpeechRateBarWidth));
            OnPropertyChanged(nameof(EyeContactBarWidth));
            OnPropertyChanged(nameof(GestureBarWidth));
            OnPropertyChanged(nameof(SilenceBarWidth));
            OnPropertyChanged(nameof(ContentBarWidth));
        }

        private void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
