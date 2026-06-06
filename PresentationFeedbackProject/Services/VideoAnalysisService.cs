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

            if (!File.Exists(scriptPath))
            {
                throw new FileNotFoundException("Python 분석 스크립트를 찾을 수 없습니다.", scriptPath);
            }

            string pythonExe = FindPythonExecutable(projectRoot);

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

            string json = ExtractJson(stdout);

            if (string.IsNullOrWhiteSpace(json))
            {
                throw new InvalidOperationException(
                    $"Python 분석 결과 JSON을 읽지 못했습니다.\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}");
            }

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

        private static string FindPythonExecutable(string projectRoot)
        {
            string? configuredPython = Environment.GetEnvironmentVariable("PYTHON_EXE");

            if (!string.IsNullOrWhiteSpace(configuredPython) && File.Exists(configuredPython))
            {
                return configuredPython;
            }

            string windowsVenvPython = Path.Combine(projectRoot, ".venv", "Scripts", "python.exe");

            if (File.Exists(windowsVenvPython))
            {
                return windowsVenvPython;
            }

            string unixVenvPython = Path.Combine(projectRoot, ".venv", "bin", "python");

            if (File.Exists(unixVenvPython))
            {
                return unixVenvPython;
            }

            return "python";
        }

        private static string ExtractJson(string text)
        {
            int start = text.IndexOf('{');
            int end = text.LastIndexOf('}');

            if (start < 0 || end < start)
            {
                return "";
            }

            return text[start..(end + 1)];
        }

        private static AnalysisResult ConvertToAnalysisResult(string json, string videoPath)
        {
            using JsonDocument document = JsonDocument.Parse(json);
            JsonElement root = document.RootElement;

            if (root.TryGetProperty("success", out JsonElement success)
                && success.ValueKind == JsonValueKind.False)
            {
                throw new InvalidOperationException(GetString(root, "error"));
            }

            JsonElement video = GetObject(root, "video");
            JsonElement audio = GetObject(root, "audio");
            JsonElement feedback = GetObject(root, "feedback");
            JsonElement scores = GetObject(feedback, "scores");

            int totalScore = GetInt(feedback, "total_score");
            int speechRateScore = ScaleScore(GetInt(scores, "speech_rate"), 20);
            int eyeContactScore = ScaleScore(GetInt(scores, "eye_contact"), 20);
            int gestureScore = ScaleScore(GetInt(scores, "gesture"), 15);
            int silenceScore = ScaleScore(GetInt(scores, "silence"), 15);
            int contentScore = (ScaleScore(GetInt(scores, "posture"), 15) + ScaleScore(GetInt(scores, "filler"), 15)) / 2;
            int wpm = GetRoundedInt(audio, "speech_rate_wpm");

            return new AnalysisResult
            {
                Wpm = wpm,

                SpeechRateScore = speechRateScore,
                EyeContactScore = eyeContactScore,
                GestureScore = gestureScore,
                SilenceScore = silenceScore,
                ContentScore = contentScore,

                TotalScore = totalScore,

                Grade = GetString(feedback, "grade"),
                OverallFeedback = BuildOverallFeedback(feedback),
                SpeedFeedback = BuildSpeedFeedback(audio),
                EyeContactFeedback = BuildVisualMetricFeedback(
                    video,
                    "eye_contact_available",
                    "eye_contact_percent",
                    "시선 처리",
                    "얼굴이 충분히 감지되지 않아 시선 평가는 제외되었습니다."),
                GestureFeedback = BuildGesturePostureFeedback(video),
                SilenceFeedback = BuildSilenceFeedback(audio),
                ContentFeedback = BuildContentFeedback(feedback),
                Transcript = GetString(audio, "transcript"),

                PresentationTopic = Path.GetFileNameWithoutExtension(videoPath),
                MainKeywords = BuildFillerText(audio),
                ContentImprovement = JoinStringArray(feedback, "improvements")
            };
        }

        private static string BuildOverallFeedback(JsonElement feedback)
        {
            string oneLine = GetString(feedback, "one_line_feedback");
            string improvements = JoinStringArray(feedback, "improvements");

            if (string.IsNullOrWhiteSpace(improvements))
            {
                return oneLine;
            }

            return $"{oneLine} 보완점: {improvements}";
        }

        private static string BuildSpeedFeedback(JsonElement audio)
        {
            if (!GetBool(audio, "available"))
            {
                return $"음성 분석을 수행하지 못했습니다. {GetString(audio, "error")}".Trim();
            }

            int wpm = GetRoundedInt(audio, "speech_rate_wpm");

            if (wpm >= 120 && wpm <= 170)
            {
                return $"발표 속도는 {wpm} WPM으로 적절한 편입니다.";
            }

            if (wpm < 120)
            {
                return $"발표 속도는 {wpm} WPM으로 느린 편입니다.";
            }

            return $"발표 속도는 {wpm} WPM으로 빠른 편입니다.";
        }

        private static string BuildVisualMetricFeedback(
            JsonElement video,
            string availablePropertyName,
            string percentPropertyName,
            string label,
            string unavailableMessage)
        {
            if (!GetBool(video, "available"))
            {
                return $"영상 분석을 수행하지 못했습니다. {GetString(video, "error")}".Trim();
            }

            if (!GetBool(video, availablePropertyName))
            {
                return unavailableMessage;
            }

            JsonElement summary = GetObject(video, "summary");
            double percent = GetDouble(summary, percentPropertyName);

            return $"{label} 비율은 {percent:0.0}%입니다.";
        }

        private static string BuildGesturePostureFeedback(JsonElement video)
        {
            if (!GetBool(video, "available"))
            {
                return $"영상 분석을 수행하지 못했습니다. {GetString(video, "error")}".Trim();
            }

            bool gestureAvailable = GetBool(video, "gesture_available");
            bool postureAvailable = GetBool(video, "posture_available");

            if (!gestureAvailable && !postureAvailable)
            {
                return "상체 관절이 충분히 감지되지 않아 손동작과 자세 평가는 제외되었습니다.";
            }

            JsonElement summary = GetObject(video, "summary");
            List<string> feedbackParts = new List<string>();

            if (gestureAvailable)
            {
                feedbackParts.Add($"제스처 사용 비율은 {GetDouble(summary, "gesture_percent"):0.0}%입니다.");
            }
            else
            {
                feedbackParts.Add("손동작 평가는 제외되었습니다.");
            }

            if (postureAvailable)
            {
                feedbackParts.Add($"자세 안정 비율은 {GetDouble(summary, "posture_stability_percent"):0.0}%입니다.");
            }
            else
            {
                feedbackParts.Add("자세 평가는 제외되었습니다.");
            }

            return string.Join(" ", feedbackParts);
        }

        private static string BuildSilenceFeedback(JsonElement audio)
        {
            if (!GetBool(audio, "available"))
            {
                return $"침묵 구간을 분석하지 못했습니다. {GetString(audio, "error")}".Trim();
            }

            JsonElement silence = GetObject(audio, "silence");
            int count = GetInt(silence, "silence_count");
            double totalSec = GetDouble(silence, "total_silence_sec");

            if (count == 0)
            {
                return "긴 침묵 구간이 거의 감지되지 않았습니다.";
            }

            return $"긴 침묵 {count}회, 총 {totalSec:0.0}초가 감지되었습니다.";
        }

        private static string BuildContentFeedback(JsonElement feedback)
        {
            string strengths = JoinStringArray(feedback, "strengths");

            if (string.IsNullOrWhiteSpace(strengths))
            {
                return GetString(feedback, "one_line_feedback");
            }

            return strengths;
        }

        private static string BuildFillerText(JsonElement audio)
        {
            JsonElement detail = GetObject(audio, "filler_detail");
            List<string> fillers = new List<string>();

            if (detail.ValueKind != JsonValueKind.Object)
            {
                return "감지된 주요 습관어 없음";
            }

            foreach (JsonProperty property in detail.EnumerateObject())
            {
                fillers.Add($"{property.Name} {GetInt(detail, property.Name)}회");
            }

            if (fillers.Count == 0)
            {
                return "감지된 주요 습관어 없음";
            }

            return string.Join(", ", fillers);
        }

        private static string JoinStringArray(JsonElement element, string propertyName)
        {
            if (element.ValueKind != JsonValueKind.Object
                || !element.TryGetProperty(propertyName, out JsonElement property)
                || property.ValueKind != JsonValueKind.Array)
            {
                return "";
            }

            List<string> values = new List<string>();

            foreach (JsonElement item in property.EnumerateArray())
            {
                if (item.ValueKind == JsonValueKind.String)
                {
                    string? value = item.GetString();

                    if (!string.IsNullOrWhiteSpace(value))
                    {
                        values.Add(value);
                    }
                }
            }

            return string.Join(" ", values);
        }

        private static JsonElement GetObject(JsonElement element, string propertyName)
        {
            return element.ValueKind == JsonValueKind.Object
                && element.TryGetProperty(propertyName, out JsonElement property)
                && property.ValueKind == JsonValueKind.Object
                    ? property
                    : default;
        }

        private static bool GetBool(JsonElement element, string propertyName)
        {
            return element.ValueKind == JsonValueKind.Object
                && element.TryGetProperty(propertyName, out JsonElement property)
                && property.ValueKind == JsonValueKind.True;
        }

        private static int GetInt(JsonElement element, string propertyName)
        {
            return element.ValueKind == JsonValueKind.Object
                && element.TryGetProperty(propertyName, out JsonElement property)
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
            return element.ValueKind == JsonValueKind.Object
                && element.TryGetProperty(propertyName, out JsonElement property)
                && property.TryGetDouble(out double value)
                    ? value
                    : 0;
        }

        private static string GetString(JsonElement element, string propertyName)
        {
            return element.ValueKind == JsonValueKind.Object
                && element.TryGetProperty(propertyName, out JsonElement property)
                && property.ValueKind == JsonValueKind.String
                    ? property.GetString() ?? ""
                    : "";
        }

        private static int ScaleScore(int value, int max)
        {
            if (max <= 0)
            {
                return 0;
            }

            return Math.Clamp((int)Math.Round(value / (double)max * 100), 0, 100);
        }
    }
}
