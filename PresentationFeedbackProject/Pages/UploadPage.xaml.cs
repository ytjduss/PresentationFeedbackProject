using System.Windows;
using System.Windows.Controls;
using PresentationFeedbackUI.Services;

namespace PresentationFeedbackUI.Pages
{
    public partial class UploadPage : Page
    {
        private readonly MainWindow mainWindow;
        private readonly VideoAnalysisService analysisService = new VideoAnalysisService();

        private string selectedVideoPath = "presentation_sample.mp4";

        public UploadPage(MainWindow mainWindow)
        {
            InitializeComponent();
            this.mainWindow = mainWindow;
        }

        private async void AnalyzeButton_Click(object sender, RoutedEventArgs e)
        {
            var result = await analysisService.AnalyzeAsync(selectedVideoPath);
            mainWindow.AnalysisViewModel.SetResult(result);
            mainWindow.NavigateToAnalysis();
        }
    }
}