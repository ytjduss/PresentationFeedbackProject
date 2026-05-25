using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using PresentationFeedbackUI.Models;

namespace PresentationFeedbackUI.Services
{
    public class VideoAnalysisService
    {
        public async Task<AnalysisResult> AnalyzeAsync(string videoPath)
        {
            if (string.IsNullOrWhiteSpace(videoPath) || !File.Exists(videoPath))
            {
                throw new FileNotFoundException("분석할 영상 파일을 찾을 수 없습니다.", videoPath);
            }

            string projectRoot = FindProjectRoot();
            string scriptPath = Path.Combine(projectRoot, "main_analysis.py");
            string outputPath = Path.Combine(
                projectRoot,
                "PythonAnalysis",
                "output",
                $"{Path.GetFileNameWithoutExtension(videoPath)}_final_analysis.json");

            if (!File.Exists(scriptPath))
            {
                throw new FileNotFoundException("Python 분석 스크립트를 찾을 수 없습니다.", scriptPath);
            }

            if (File.Exists(outputPath))
            {
                File.Delete(outputPath);
            }

            string pythonExe = Environment.GetEnvironmentVariable("PYTHON_EXE") ?? "python";

            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = pythonExe,
                WorkingDirectory = projectRoot,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            startInfo.ArgumentList.Add(scriptPath);
            startInfo.ArgumentList.Add(videoPath);
            startInfo.ArgumentList.Add("small");

            using Process process = Process.Start(startInfo)
                ?? throw new InvalidOperationException("Python 프로세스를 시작하지 못했습니다.");

            Task<string> stdoutTask = process.StandardOutput.ReadToEndAsync();
            Task<string> stderrTask = process.StandardError.ReadToEndAsync();

            await process.WaitForExitAsync();

            string stdout = await stdoutTask;
            string stderr = await stderrTask;

            if (process.ExitCode != 0)
            {
                throw new InvalidOperationException(
                    $"Python 분석이 실패했습니다.\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}");
            }

            if (!File.Exists(outputPath))
            {
                throw new FileNotFoundException("Python 분석 결과 JSON을 찾을 수 없습니다.", outputPath);
            }

            string json = await File.ReadAllTextAsync(outputPath, Encoding.UTF8);
            return ConvertToAnalysisResult(json, videoPath);
        }

        private static string FindProjectRoot()
        {
            DirectoryInfo? directory = new DirectoryInfo(AppContext.BaseDirectory);

            while (directory != null)
            {
                if (File.Exists(Path.Combine(directory.FullName, "main_analysis.py"))
                    && Directory.Exists(Path.Combine(directory.FullName, "PythonAnalysis")))
                {
                    return directory.FullName;
                }

                directory = directory.Parent;
            }

            throw new DirectoryNotFoundException("프로젝트 루트 폴더를 찾을 수 없습니다.");
        }

        private static AnalysisResult ConvertToAnalysisResult(string json, string videoPath)
        {
            using JsonDocument document = JsonDocument.Parse(json);
            JsonElement root = document.RootElement;
            JsonElement summary = root.GetProperty("summary");

            JsonElement speechSpeed = summary.GetProperty("speechSpeed");
            JsonElement gaze = summary.GetProperty("gaze");
            JsonElement gesture = summary.GetProperty("gesture");
            JsonElement content = summary.GetProperty("content");

            int wpm = GetRoundedInt(speechSpeed, "wordsPerMinute");
            int speechRateScore = CalculateSpeechRateScore(GetDouble(speechSpeed, "syllablesPerSec"));
            int eyeContactScore = ClampScore(GetDouble(gaze, "frontRatio") * 100);
            int gestureScore = ClampScore(GetDouble(gesture, "movementScore") / 25 * 100);
            int silenceScore = CalculateSilenceScore(
                GetInt(summary, "pauseCount"),
                GetInt(summary, "hesitationCount"));
            int contentScore = CalculateContentScore(content);
            int totalScore = (speechRateScore + eyeContactScore + gestureScore + silenceScore + contentScore) / 5;

            return new AnalysisResult
            {
                Wpm = wpm,

                SpeechRateScore = speechRateScore,
                EyeContactScore = eyeContactScore,
                GestureScore = gestureScore,
                SilenceScore = silenceScore,
                ContentScore = contentScore,

                TotalScore = totalScore,

                OverallFeedback = GetString(summary, "overallFeedback"),
                SpeedFeedback = GetString(speechSpeed, "feedback"),
                EyeContactFeedback = GetString(gaze, "feedback"),
                GestureFeedback = GetString(gesture, "feedback"),
                SilenceFeedback = BuildSilenceFeedback(summary),
                ContentFeedback = GetString(content, "contentFeedback"),

                PresentationTopic = Path.GetFileNameWithoutExtension(videoPath),
                MainKeywords = BuildKeywordText(content),
                ContentImprovement = $"{GetString(content, "lengthFeedback")} {GetString(content, "clarityFeedback")}".Trim()
            };
        }

        private static int CalculateSpeechRateScore(double syllablesPerSec)
        {
            if (syllablesPerSec <= 0)
            {
                return 0;
            }

            if (syllablesPerSec >= 2.5 && syllablesPerSec <= 4.0)
            {
                return 100;
            }

            double distance = syllablesPerSec < 2.5
                ? 2.5 - syllablesPerSec
                : syllablesPerSec - 4.0;

            return ClampScore(100 - distance * 25);
        }

        private static int CalculateSilenceScore(int pauseCount, int hesitationCount)
        {
            return ClampScore(100 - pauseCount * 8 - hesitationCount * 3);
        }

        private static int CalculateContentScore(JsonElement content)
        {
            string lengthLabel = GetString(content, "lengthLabel");
            double avgWordsPerSentence = GetDouble(content, "avgWordsPerSentence");

            int score = lengthLabel == "적절" ? 90 : 72;

            if (avgWordsPerSentence > 25)
            {
                score -= 12;
            }

            return ClampScore(score);
        }

        private static string BuildSilenceFeedback(JsonElement summary)
        {
            int pauseCount = GetInt(summary, "pauseCount");
            int hesitationCount = GetInt(summary, "hesitationCount");

            if (pauseCount == 0 && hesitationCount == 0)
            {
                return "침묵 구간과 발화 끊김이 적어 발표 흐름이 안정적입니다.";
            }

            return $"긴 침묵 {pauseCount}회, 짧은 발화 끊김 {hesitationCount}회가 감지되었습니다.";
        }

        private static string BuildKeywordText(JsonElement content)
        {
            if (!content.TryGetProperty("keywords", out JsonElement keywords)
                || keywords.ValueKind != JsonValueKind.Array)
            {
                return "";
            }

            List<string> keywordTexts = new List<string>();

            foreach (JsonElement keyword in keywords.EnumerateArray())
            {
                string text = GetString(keyword, "keyword");

                if (!string.IsNullOrWhiteSpace(text))
                {
                    keywordTexts.Add(text);
                }
            }

            return string.Join(", ", keywordTexts);
        }

        private static int GetInt(JsonElement element, string propertyName)
        {
            return element.TryGetProperty(propertyName, out JsonElement property)
                && property.TryGetInt32(out int value)
                    ? value
                    : 0;
        }

        private static int GetRoundedInt(JsonElement element, string propertyName)
        {
            return (int)Math.Round(GetDouble(element, propertyName));
        }

        private static double GetDouble(JsonElement element, string propertyName)
        {
            return element.TryGetProperty(propertyName, out JsonElement property)
                && property.TryGetDouble(out double value)
                    ? value
                    : 0;
        }

        private static string GetString(JsonElement element, string propertyName)
        {
            return element.TryGetProperty(propertyName, out JsonElement property)
                && property.ValueKind == JsonValueKind.String
                    ? property.GetString() ?? ""
                    : "";
        }

        private static int ClampScore(double value)
        {
            return Math.Clamp((int)Math.Round(value), 0, 100);
        }
    }
}
