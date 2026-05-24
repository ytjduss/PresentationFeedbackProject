using System.Windows;
using System.Windows.Media;
using PresentationFeedbackUI.Pages;
using PresentationFeedbackUI.ViewModels;

namespace PresentationFeedbackUI
{
    public partial class MainWindow : Window
    {
        public AnalysisViewModel AnalysisViewModel { get; } = new AnalysisViewModel();

        public MainWindow()
        {
            InitializeComponent();
            NavigateToLogin();
        }

        public void NavigateToLogin()
        {
            SetStep(1);
            MainFrame.Navigate(new LoginPage(this));
        }

        public void NavigateToUpload()
        {
            SetStep(1);
            MainFrame.Navigate(new UploadPage(this));
        }

        public void NavigateToAnalysis()
        {
            SetStep(3);
            MainFrame.Navigate(new AnalysisPage(this));
        }

        public void NavigateToScore()
        {
            SetStep(4);
            MainFrame.Navigate(new ScorePage(this));
        }

        private void SetStep(int step)
        {
            Brush mint = (Brush)FindResource("MintBrush");
            Brush gray = (Brush)FindResource("GrayBrush");
            Brush textGray = (Brush)FindResource("TextGrayBrush");

            StepCircle1.Background = step >= 1 ? mint : gray;
            StepCircle2.Background = step >= 2 ? mint : gray;
            StepCircle3.Background = step >= 3 ? mint : gray;
            StepCircle4.Background = step >= 4 ? mint : gray;

            StepText1.Foreground = step >= 1 ? mint : textGray;
            StepText2.Foreground = step >= 2 ? mint : textGray;
            StepText3.Foreground = step >= 3 ? mint : textGray;
            StepText4.Foreground = step >= 4 ? mint : textGray;
        }
    }
}