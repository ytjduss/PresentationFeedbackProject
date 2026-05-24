using System.Windows;
using System.Windows.Controls;

namespace PresentationFeedbackUI.Pages
{
    public partial class ScorePage : Page
    {
        private readonly MainWindow mainWindow;

        public ScorePage(MainWindow mainWindow)
        {
            InitializeComponent();
            this.mainWindow = mainWindow;
            DataContext = mainWindow.AnalysisViewModel;
        }

        private void UploadButton_Click(object sender, RoutedEventArgs e)
        {
            mainWindow.NavigateToUpload();
        }
    }
}