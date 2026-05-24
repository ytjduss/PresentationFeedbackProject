using System.Threading.Tasks;
using PresentationFeedbackUI.Models;

namespace PresentationFeedbackUI.Services
{
    public class VideoAnalysisService
    {
        public async Task<AnalysisResult> AnalyzeAsync(string videoPath)
        {
            await Task.Delay(1500);

            return new AnalysisResult
            {
                Wpm = 132,

                SpeechRateScore = 82,
                EyeContactScore = 88,
                GestureScore = 74,
                SilenceScore = 85,
                ContentScore = 84,

                TotalScore = 83,

                OverallFeedback = "전체적으로 안정적인 발표였어요! 시선 처리와 침묵 구간은 좋았습니다. 다만 손동작과 발표 내용의 마무리 구조를 조금 더 보완하면 전달력이 높아질 수 있습니다.",
                SpeedFeedback = "말 빠르기는 적절한 편입니다. 핵심 문장 뒤에는 짧은 쉼을 유지하세요.",
                EyeContactFeedback = "정면 응시가 안정적입니다.",
                GestureFeedback = "강조 동작이 다소 부족합니다.",
                SilenceFeedback = "문장 사이 공백은 적절한 편입니다.",
                ContentFeedback = "발표 주제와 핵심 키워드는 잘 드러나지만 결론 요약이 조금 부족합니다.",

                PresentationTopic = "발표 피드백 프로그램",
                MainKeywords = "말빠르기, 시선 처리, 손동작, 침묵 구간, 발표 내용",
                ContentImprovement = "결론 부분에서 핵심 내용을 한 번 더 요약하면 좋습니다."
            };
        }
    }
}