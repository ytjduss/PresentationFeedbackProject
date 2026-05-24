using System.Windows;
using System.Windows.Controls;

namespace PresentationFeedbackUI.Pages
{
    public partial class LoginPage : Page
    {
        private readonly MainWindow mainWindow;

        public LoginPage(MainWindow mainWindow)
        {
            InitializeComponent();
            this.mainWindow = mainWindow;
        }

        private void LoginButton_Click(object sender, RoutedEventArgs e)
        {
            mainWindow.NavigateToUpload();
        }
    }
}