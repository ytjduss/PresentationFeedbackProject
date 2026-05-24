using System.Windows;
using System.Windows.Controls;
using PresentationFeedbackUI.Services;
using PresentationFeedbackUI.Models;

namespace PresentationFeedbackUI.Pages
{
    public partial class LoginPage : Page
    {
        private readonly MainWindow mainWindow;
        private readonly AuthService authService = new AuthService();

        public LoginPage(MainWindow mainWindow)
        {
            InitializeComponent();
            this.mainWindow = mainWindow;
        }

        private void LoginButton_Click(object sender, RoutedEventArgs e)
        {
            string username = UsernameTextBox.Text.Trim();
            string password = PasswordBox.Password.Trim();

            if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password))
            {
                MessageBox.Show("아이디와 비밀번호를 입력하세요.");
                return;
            }

            User? user = authService.Login(username, password);

            if (user == null)
            {
                MessageBox.Show("아이디 또는 비밀번호가 올바르지 않습니다.");
                return;
            }

            MessageBox.Show($"{user.DisplayName}님 환영합니다.");
            mainWindow.NavigateToUpload();
        }

        private void GuestButton_Click(object sender, RoutedEventArgs e)
        {
            User guest = new User
            {
                Id = 0,
                Username = "guest",
                DisplayName = "게스트"
            };

            SessionManager.Login(guest);
            mainWindow.NavigateToUpload();
        }

        private void SignupButton_Click(object sender, RoutedEventArgs e)
        {
            mainWindow.NavigateToSignup();
        }
    }
}