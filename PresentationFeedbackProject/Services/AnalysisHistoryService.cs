using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Microsoft.Data.Sqlite;
using PresentationFeedbackUI.Database;
using PresentationFeedbackUI.Models;

namespace PresentationFeedbackUI.Services
{
    public class AnalysisHistoryService
    {
        public void Save(int userId, string videoPath, AnalysisResult result)
        {
            if (userId <= 0)
            {
                return;
            }

            using var connection = new SqliteConnection(DbManager.ConnectionString);
            connection.Open();

            using var command = connection.CreateCommand();
            command.CommandText = @"
                INSERT INTO analysis_results (
                    user_id,
                    video_path,
                    video_name,
                    total_score,
                    speech_rate_score,
                    eye_contact_score,
                    gesture_score,
                    silence_score,
                    content_score,
                    wpm,
                    grade,
                    overall_feedback,
                    speed_feedback,
                    eye_contact_feedback,
                    gesture_feedback,
                    silence_feedback,
                    content_feedback,
                    transcript,
                    presentation_topic,
                    main_keywords,
                    content_improvement,
                    created_at
                )
                VALUES (
                    @user_id,
                    @video_path,
                    @video_name,
                    @total_score,
                    @speech_rate_score,
                    @eye_contact_score,
                    @gesture_score,
                    @silence_score,
                    @content_score,
                    @wpm,
                    @grade,
                    @overall_feedback,
                    @speed_feedback,
                    @eye_contact_feedback,
                    @gesture_feedback,
                    @silence_feedback,
                    @content_feedback,
                    @transcript,
                    @presentation_topic,
                    @main_keywords,
                    @content_improvement,
                    @created_at
                );
            ";

            command.Parameters.AddWithValue("@user_id", userId);
            command.Parameters.AddWithValue("@video_path", videoPath);
            command.Parameters.AddWithValue("@video_name", Path.GetFileName(videoPath));
            command.Parameters.AddWithValue("@total_score", result.TotalScore);
            command.Parameters.AddWithValue("@speech_rate_score", result.SpeechRateScore);
            command.Parameters.AddWithValue("@eye_contact_score", result.EyeContactScore);
            command.Parameters.AddWithValue("@gesture_score", result.GestureScore);
            command.Parameters.AddWithValue("@silence_score", result.SilenceScore);
            command.Parameters.AddWithValue("@content_score", result.ContentScore);
            command.Parameters.AddWithValue("@wpm", result.Wpm);
            command.Parameters.AddWithValue("@grade", result.Grade);
            command.Parameters.AddWithValue("@overall_feedback", result.OverallFeedback);
            command.Parameters.AddWithValue("@speed_feedback", result.SpeedFeedback);
            command.Parameters.AddWithValue("@eye_contact_feedback", result.EyeContactFeedback);
            command.Parameters.AddWithValue("@gesture_feedback", result.GestureFeedback);
            command.Parameters.AddWithValue("@silence_feedback", result.SilenceFeedback);
            command.Parameters.AddWithValue("@content_feedback", result.ContentFeedback);
            command.Parameters.AddWithValue("@transcript", result.Transcript);
            command.Parameters.AddWithValue("@presentation_topic", result.PresentationTopic);
            command.Parameters.AddWithValue("@main_keywords", result.MainKeywords);
            command.Parameters.AddWithValue("@content_improvement", result.ContentImprovement);
            command.Parameters.AddWithValue("@created_at", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));

            command.ExecuteNonQuery();
        }

        public List<AnalysisHistoryItem> GetByUser(int userId)
        {
            List<AnalysisHistoryItem> items = new List<AnalysisHistoryItem>();

            if (userId <= 0)
            {
                return items;
            }

            using var connection = new SqliteConnection(DbManager.ConnectionString);
            connection.Open();

            using var command = connection.CreateCommand();
            command.CommandText = @"
                SELECT
                    id,
                    user_id,
                    video_path,
                    video_name,
                    total_score,
                    speech_rate_score,
                    eye_contact_score,
                    gesture_score,
                    silence_score,
                    content_score,
                    wpm,
                    grade,
                    overall_feedback,
                    speed_feedback,
                    eye_contact_feedback,
                    gesture_feedback,
                    silence_feedback,
                    content_feedback,
                    transcript,
                    presentation_topic,
                    main_keywords,
                    content_improvement,
                    created_at
                FROM analysis_results
                WHERE user_id = @user_id
                ORDER BY datetime(created_at) DESC, id DESC;
            ";
            command.Parameters.AddWithValue("@user_id", userId);

            using var reader = command.ExecuteReader();

            while (reader.Read())
            {
                items.Add(new AnalysisHistoryItem
                {
                    Id = reader.GetInt32(0),
                    UserId = reader.GetInt32(1),
                    VideoPath = ReadString(reader, 2),
                    VideoName = ReadString(reader, 3),
                    Result = new AnalysisResult
                    {
                        TotalScore = reader.GetInt32(4),
                        SpeechRateScore = reader.GetInt32(5),
                        EyeContactScore = reader.GetInt32(6),
                        GestureScore = reader.GetInt32(7),
                        SilenceScore = reader.GetInt32(8),
                        ContentScore = reader.GetInt32(9),
                        Wpm = reader.GetInt32(10),
                        Grade = ReadString(reader, 11),
                        OverallFeedback = ReadString(reader, 12),
                        SpeedFeedback = ReadString(reader, 13),
                        EyeContactFeedback = ReadString(reader, 14),
                        GestureFeedback = ReadString(reader, 15),
                        SilenceFeedback = ReadString(reader, 16),
                        ContentFeedback = ReadString(reader, 17),
                        Transcript = ReadString(reader, 18),
                        PresentationTopic = ReadString(reader, 19),
                        MainKeywords = ReadString(reader, 20),
                        ContentImprovement = ReadString(reader, 21)
                    },
                    CreatedAt = ParseDate(ReadString(reader, 22))
                });
            }

            return items;
        }

        private static string ReadString(SqliteDataReader reader, int index)
        {
            return reader.IsDBNull(index) ? "" : reader.GetString(index);
        }

        private static DateTime ParseDate(string value)
        {
            return DateTime.TryParseExact(
                value,
                "yyyy-MM-dd HH:mm:ss",
                CultureInfo.InvariantCulture,
                DateTimeStyles.None,
                out DateTime parsed)
                    ? parsed
                    : DateTime.MinValue;
        }
    }
}
