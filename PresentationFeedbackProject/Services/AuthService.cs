using Microsoft.Data.Sqlite;
using PresentationFeedbackUI.Database;
using System;
using PresentationFeedbackUI.Models;

namespace PresentationFeedbackUI.Services
{
    public class AuthService
    {
        public bool Register(string username, string password, string displayName, out string message)
        {
            if (string.IsNullOrWhiteSpace(username))
            {
                message = "아이디를 입력하세요.";
                return false;
            }

            if (string.IsNullOrWhiteSpace(password))
            {
                message = "비밀번호를 입력하세요.";
                return false;
            }

            if (string.IsNullOrWhiteSpace(displayName))
            {
                message = "이름을 입력하세요.";
                return false;
            }

            if (username.Length < 4)
            {
                message = "아이디는 4자 이상이어야 합니다.";
                return false;
            }

            if (password.Length < 4)
            {
                message = "비밀번호는 4자 이상이어야 합니다.";
                return false;
            }

            using var connection = new SqliteConnection(DbManager.ConnectionString);
            connection.Open();

            using var checkCommand = connection.CreateCommand();
            checkCommand.CommandText = "SELECT COUNT(*) FROM users WHERE username = @username";
            checkCommand.Parameters.AddWithValue("@username", username);

            long count = (long)checkCommand.ExecuteScalar()!;

            if (count > 0)
            {
                message = "이미 사용 중인 아이디입니다.";
                return false;
            }

            string passwordHash = PasswordHasher.HashPassword(password);

            using var insertCommand = connection.CreateCommand();
            insertCommand.CommandText = @"
                INSERT INTO users (username, password_hash, display_name, created_at)
                VALUES (@username, @password_hash, @display_name, @created_at);
            ";

            insertCommand.Parameters.AddWithValue("@username", username);
            insertCommand.Parameters.AddWithValue("@password_hash", passwordHash);
            insertCommand.Parameters.AddWithValue("@display_name", displayName);
            insertCommand.Parameters.AddWithValue("@created_at", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));

            insertCommand.ExecuteNonQuery();

            message = "회원가입이 완료되었습니다.";
            return true;
        }

        public User? Login(string username, string password)
        {
            if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password))
            {
                return null;
            }

            using var connection = new SqliteConnection(DbManager.ConnectionString);
            connection.Open();

            using var command = connection.CreateCommand();
            command.CommandText = "SELECT id, username, password_hash, display_name FROM users WHERE username = @username";
            command.Parameters.AddWithValue("@username", username);

            using var reader = command.ExecuteReader();

            if (!reader.Read())
            {
                return null;
            }

            int id = reader.GetInt32(0);
            string dbUsername = reader.GetString(1);
            string passwordHash = reader.GetString(2);
            string displayName = reader.GetString(3);

            string providedHash = PasswordHasher.HashPassword(password);

            if (passwordHash != providedHash)
            {
                return null;
            }

            var user = new User
            {
                Id = id,
                Username = dbUsername,
                DisplayName = displayName
            };

            SessionManager.Login(user);

            using var updateCmd = connection.CreateCommand();
            updateCmd.CommandText = "UPDATE users SET last_login_at = @last_login WHERE id = @id";
            updateCmd.Parameters.AddWithValue("@last_login", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            updateCmd.Parameters.AddWithValue("@id", id);
            updateCmd.ExecuteNonQuery();

            return user;
        }

        public void Logout()
        {
            SessionManager.Logout();
        }
    }
}