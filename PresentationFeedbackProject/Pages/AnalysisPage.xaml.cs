using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace PresentationFeedbackUI.Pages
{
    public partial class AnalysisPage : Page
    {
        private readonly MainWindow mainWindow;
        private readonly DispatcherTimer videoTimer = new DispatcherTimer();

        private bool isDraggingTimeline = false;

        public AnalysisPage(MainWindow mainWindow)
        {
            InitializeComponent();

            this.mainWindow = mainWindow;
            DataContext = mainWindow.AnalysisViewModel;

            videoTimer.Interval = TimeSpan.FromMilliseconds(300);
            videoTimer.Tick += VideoTimer_Tick;

            LoadVideo();
        }

        private void LoadVideo()
        {
            string videoPath = mainWindow.SelectedVideoPath;

            if (string.IsNullOrWhiteSpace(videoPath) || !File.Exists(videoPath))
            {
                NoVideoText.Visibility = Visibility.Visible;
                VideoFileNameText.Text = "선택된 영상 없음";
                VideoTimeText.Text = "00:00 / 00:00";
                return;
            }

            AnalysisVideoPlayer.Source = new Uri(videoPath, UriKind.Absolute);
            AnalysisVideoPlayer.Position = TimeSpan.Zero;

            NoVideoText.Visibility = Visibility.Collapsed;
            VideoFileNameText.Text = Path.GetFileName(videoPath);

            AnalysisVideoPlayer.MediaOpened += AnalysisVideoPlayer_MediaOpened;
            AnalysisVideoPlayer.MediaEnded += AnalysisVideoPlayer_MediaEnded;

            AnalysisVideoPlayer.Play();
            videoTimer.Start();
        }

        private void AnalysisVideoPlayer_MediaOpened(object sender, RoutedEventArgs e)
        {
            if (AnalysisVideoPlayer.NaturalDuration.HasTimeSpan)
            {
                TimeSpan duration = AnalysisVideoPlayer.NaturalDuration.TimeSpan;
                VideoTimelineSlider.Maximum = duration.TotalSeconds;
                VideoTimeText.Text = $"00:00 / {FormatTime(duration)}";
            }
        }

        private void VideoTimer_Tick(object? sender, EventArgs e)
        {
            if (AnalysisVideoPlayer.Source == null)
            {
                return;
            }

            if (!AnalysisVideoPlayer.NaturalDuration.HasTimeSpan)
            {
                return;
            }

            TimeSpan current = AnalysisVideoPlayer.Position;
            TimeSpan total = AnalysisVideoPlayer.NaturalDuration.TimeSpan;

            if (!isDraggingTimeline)
            {
                VideoTimelineSlider.Value = current.TotalSeconds;
            }

            VideoTimeText.Text = $"{FormatTime(current)} / {FormatTime(total)}";
        }

        private void VideoTimelineSlider_PreviewMouseDown(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            isDraggingTimeline = true;
        }

        private void VideoTimelineSlider_PreviewMouseUp(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            if (AnalysisVideoPlayer.Source != null)
            {
                AnalysisVideoPlayer.Position = TimeSpan.FromSeconds(VideoTimelineSlider.Value);
            }

            isDraggingTimeline = false;
        }

        private void VideoPlayButton_Click(object sender, RoutedEventArgs e)
        {
            if (AnalysisVideoPlayer.Source != null)
            {
                AnalysisVideoPlayer.Play();
                videoTimer.Start();
            }
        }

        private void VideoPauseButton_Click(object sender, RoutedEventArgs e)
        {
            if (AnalysisVideoPlayer.Source != null)
            {
                AnalysisVideoPlayer.Pause();
            }
        }

        private void VideoRestartButton_Click(object sender, RoutedEventArgs e)
        {
            if (AnalysisVideoPlayer.Source != null)
            {
                AnalysisVideoPlayer.Stop();
                AnalysisVideoPlayer.Position = TimeSpan.Zero;
                AnalysisVideoPlayer.Play();
                videoTimer.Start();
            }
        }

        private void AnalysisVideoPlayer_MediaEnded(object sender, RoutedEventArgs e)
        {
            videoTimer.Stop();
            AnalysisVideoPlayer.Stop();
            AnalysisVideoPlayer.Position = TimeSpan.Zero;
            VideoTimelineSlider.Value = 0;
        }

        private string FormatTime(TimeSpan time)
        {
            return $"{(int)time.TotalMinutes:00}:{time.Seconds:00}";
        }

        private void ScoreButton_Click(object sender, RoutedEventArgs e)
        {
            videoTimer.Stop();

            if (AnalysisVideoPlayer.Source != null)
            {
                AnalysisVideoPlayer.Stop();
            }

            mainWindow.NavigateToScore();
        }
    }
}