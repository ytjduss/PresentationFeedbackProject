using System.Windows;
using System.Windows.Controls;

using PresentationFeedbackUI.Services;

namespace PresentationFeedbackUI.Pages
{
    public partial class SignupPage : Page
    {
        private readonly MainWindow mainWindow;
        private readonly AuthService authService = new AuthService();

        public SignupPage(MainWindow mainWindow)
        {
            InitializeComponent();
            this.mainWindow = mainWindow;
        }

        private void RegisterButton_Click(object sender, RoutedEventArgs e)
        {
            string username = UsernameTextBox.Text.Trim();
            string displayName = DisplayNameTextBox.Text.Trim();
            string password = PasswordBox.Password.Trim();
            string passwordConfirm = PasswordConfirmBox.Password.Trim();

            if (password != passwordConfirm)
            {
                MessageBox.Show("비밀번호가 일치하지 않습니다.");
                return;
            }

            bool success = authService.Register(username, password, displayName, out string message);

            MessageBox.Show(message);

            if (success)
            {
                mainWindow.NavigateToLogin();
            }
        }

        private void BackLoginButton_Click(object sender, RoutedEventArgs e)
        {
            mainWindow.NavigateToLogin();
        }
    }
}