using Microsoft.Data.Sqlite;
using System;
using System.IO;

namespace PresentationFeedbackUI.Database
{
    public static class DbManager
    {
        private static readonly string DbFolder =
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "PresentationPractice");

        private static readonly string DbPath =
            Path.Combine(DbFolder, "speech_practice.db");

        public static string ConnectionString => $"Data Source={DbPath}";

        public static void InitializeDatabase()
        {
            if (!Directory.Exists(DbFolder))
            {
                Directory.CreateDirectory(DbFolder);
            }

            using var connection = new SqliteConnection(ConnectionString);
            connection.Open();

            string createUsersTable = @"
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                );
            ";

            string createLoginLogsTable = @"
                CREATE TABLE IF NOT EXISTS login_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            ";

            string createAnalysisResultsTable = @"
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    video_path TEXT NOT NULL,
                    video_name TEXT,
                    total_score INTEGER NOT NULL,
                    speech_rate_score INTEGER NOT NULL,
                    eye_contact_score INTEGER NOT NULL,
                    gesture_score INTEGER NOT NULL,
                    silence_score INTEGER NOT NULL,
                    content_score INTEGER NOT NULL,
                    wpm INTEGER NOT NULL,
                    grade TEXT,
                    overall_feedback TEXT,
                    speed_feedback TEXT,
                    eye_contact_feedback TEXT,
                    gesture_feedback TEXT,
                    silence_feedback TEXT,
                    content_feedback TEXT,
                    transcript TEXT,
                    presentation_topic TEXT,
                    main_keywords TEXT,
                    content_improvement TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            ";

            ExecuteNonQuery(connection, createUsersTable);
            ExecuteNonQuery(connection, createLoginLogsTable);
            ExecuteNonQuery(connection, createAnalysisResultsTable);
            EnsureAnalysisResultColumns(connection);

            SeedDefaultUser(connection);
        }

        private static void ExecuteNonQuery(SqliteConnection connection, string sql)
        {
            using var command = connection.CreateCommand();
            command.CommandText = sql;
            command.ExecuteNonQuery();
        }

        private static void EnsureAnalysisResultColumns(SqliteConnection connection)
        {
            AddColumnIfMissing(connection, "analysis_results", "video_name", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "grade", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "speed_feedback", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "eye_contact_feedback", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "gesture_feedback", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "silence_feedback", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "content_feedback", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "transcript", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "presentation_topic", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "main_keywords", "TEXT");
            AddColumnIfMissing(connection, "analysis_results", "content_improvement", "TEXT");
        }

        private static void AddColumnIfMissing(SqliteConnection connection, string tableName, string columnName, string columnType)
        {
            bool exists = false;

            {
                using var checkCommand = connection.CreateCommand();
                checkCommand.CommandText = $"PRAGMA table_info({tableName});";

                using var reader = checkCommand.ExecuteReader();

                while (reader.Read())
                {
                    if (reader.GetString(1).Equals(columnName, StringComparison.OrdinalIgnoreCase))
                    {
                        exists = true;
                        break;
                    }
                }
            }

            if (exists)
            {
                return;
            }

            using var alterCommand = connection.CreateCommand();
            alterCommand.CommandText = $"ALTER TABLE {tableName} ADD COLUMN {columnName} {columnType};";
            alterCommand.ExecuteNonQuery();
        }

        private static void SeedDefaultUser(SqliteConnection connection)
        {
            using var checkCommand = connection.CreateCommand();
            checkCommand.CommandText = "SELECT COUNT(*) FROM users WHERE username = @username";
            checkCommand.Parameters.AddWithValue("@username", "student01");

            long count = (long)checkCommand.ExecuteScalar()!;

            if (count > 0)
            {
                return;
            }

            string passwordHash = PasswordHasher.HashPassword("1234");

            using var insertCommand = connection.CreateCommand();
            insertCommand.CommandText = @"
                INSERT INTO users (username, password_hash, display_name, created_at)
                VALUES (@username, @password_hash, @display_name, @created_at);
            ";

            insertCommand.Parameters.AddWithValue("@username", "student01");
            insertCommand.Parameters.AddWithValue("@password_hash", passwordHash);
            insertCommand.Parameters.AddWithValue("@display_name", "학생");
            insertCommand.Parameters.AddWithValue("@created_at", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));

            insertCommand.ExecuteNonQuery();
        }
    }
}
