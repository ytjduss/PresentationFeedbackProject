using System.Windows;
using System.Windows.Controls;

namespace PresentationFeedbackUI.Pages
{
    public partial class AnalysisPage : Page
    {
        private readonly MainWindow mainWindow;

        public AnalysisPage(MainWindow mainWindow)
        {
            InitializeComponent();
            this.mainWindow = mainWindow;
            DataContext = mainWindow.AnalysisViewModel;
        }

        private void ScoreButton_Click(object sender, RoutedEventArgs e)
        {
            mainWindow.NavigateToScore();
        }
    }
}