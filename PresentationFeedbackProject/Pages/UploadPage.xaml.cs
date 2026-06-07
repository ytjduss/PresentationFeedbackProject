using Microsoft.Win32;
using System;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using PresentationFeedbackUI.Models;
using PresentationFeedbackUI.Services;

namespace PresentationFeedbackUI.Pages
{
    public partial class UploadPage : Page
    {
        private readonly MainWindow mainWindow;
        private readonly VideoAnalysisService analysisService = new VideoAnalysisService();
        private readonly AnalysisHistoryService historyService = new AnalysisHistoryService();

        private string selectedVideoPath = "";

        private readonly string[] allowedExtensions =
        {
            ".mp4", ".mov", ".avi"
        };

        public UploadPage(MainWindow mainWindow)
        {
            InitializeComponent();
            this.mainWindow = mainWindow;
            LoadHistory();
        }

        private void SelectFileButton_Click(object sender, RoutedEventArgs e)
        {
            OpenFileDialog dialog = new OpenFileDialog
            {
                Title = "발표 영상 선택",
                Filter = "Video Files (*.mp4;*.mov;*.avi)|*.mp4;*.mov;*.avi",
                Multiselect = false
            };

            bool? result = dialog.ShowDialog();

            if (result == true)
            {
                SetSelectedVideo(dialog.FileName);
            }
        }

        private void DropZoneBorder_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            SelectFileButton_Click(sender, e);
        }

        private void DropZoneBorder_DragEnter(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                DropZoneBorder.BorderBrush = Brushes.Black;
                DropZoneBorder.Background = (Brush)FindResource("MintBrush");
                e.Effects = DragDropEffects.Copy;
            }
            else
            {
                e.Effects = DragDropEffects.None;
            }
        }

        private void DropZoneBorder_DragLeave(object sender, DragEventArgs e)
        {
            ResetDropZoneStyle();
        }

        private void DropZoneBorder_Drop(object sender, DragEventArgs e)
        {
            ResetDropZoneStyle();

            if (!e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                return;
            }

            string[] files = (string[])e.Data.GetData(DataFormats.FileDrop);

            if (files == null || files.Length == 0)
            {
                return;
            }

            SetSelectedVideo(files[0]);
        }

        private void SetSelectedVideo(string filePath)
        {
            if (!File.Exists(filePath))
            {
                MessageBox.Show("파일을 찾을 수 없습니다.");
                return;
            }

            string extension = Path.GetExtension(filePath).ToLower();

            if (!allowedExtensions.Contains(extension))
            {
                MessageBox.Show("지원하지 않는 파일 형식입니다. MP4, MOV, AVI 파일만 업로드할 수 있습니다.");
                return;
            }

            selectedVideoPath = filePath;
            mainWindow.SelectedVideoPath = selectedVideoPath;

            FileInfo fileInfo = new FileInfo(filePath);

            SelectedFileNameText.Text = fileInfo.Name;
            SelectedFileSizeText.Text = FormatFileSize(fileInfo.Length);

            FileInfoBorder.Visibility = Visibility.Visible;
            AnalyzeButton.IsEnabled = true;

            UploadStatusText.Text = "영상 업로드가 완료되었습니다. 분석을 시작할 수 있습니다.";
        }

        private string FormatFileSize(long bytes)
        {
            double size = bytes;

            if (size < 1024)
            {
                return $"{size:0} B";
            }

            size /= 1024;

            if (size < 1024)
            {
                return $"{size:0.0} KB";
            }

            size /= 1024;

            if (size < 1024)
            {
                return $"{size:0.0} MB";
            }

            size /= 1024;

            return $"{size:0.0} GB";
        }

        private void ResetDropZoneStyle()
        {
            DropZoneBorder.BorderBrush = (Brush)FindResource("MintBrush");
            DropZoneBorder.Background = (Brush)FindResource("MintLightBrush");
        }

        private async void AnalyzeButton_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(selectedVideoPath))
            {
                MessageBox.Show("먼저 영상을 업로드해주세요.");
                return;
            }

            try
            {
                AnalyzeButton.IsEnabled = false;
                AnalyzeButton.Content = "분석 중...";

                mainWindow.SelectedVideoPath = selectedVideoPath;

                var result = await analysisService.AnalyzeAsync(selectedVideoPath);

                mainWindow.AnalysisViewModel.SetResult(result);

                if (SessionManager.CurrentUser != null)
                {
                    historyService.Save(SessionManager.CurrentUser.Id, selectedVideoPath, result);
                    LoadHistory();
                }

                mainWindow.NavigateToAnalysis();
            }
            catch (Exception ex)
            {
                MessageBox.Show("분석 중 오류가 발생했습니다.\n" + ex.Message);
            }
            finally
            {
                AnalyzeButton.Content = "분석 시작하기  →";
                AnalyzeButton.IsEnabled = true;
            }
        }

        private void LoadHistory()
        {
            if (SessionManager.CurrentUser == null)
            {
                HistoryListBox.ItemsSource = null;
                return;
            }

            HistoryListBox.ItemsSource = historyService.GetByUser(SessionManager.CurrentUser.Id);
        }

        private void OpenHistoryButton_Click(object sender, RoutedEventArgs e)
        {
            if (HistoryListBox.SelectedItem is not AnalysisHistoryItem item)
            {
                MessageBox.Show("다시 볼 분석 기록을 선택해주세요.");
                return;
            }

            if (!File.Exists(item.VideoPath))
            {
                MessageBox.Show("저장된 영상 파일을 찾을 수 없습니다.\n" + item.VideoPath);
                return;
            }

            mainWindow.SelectedVideoPath = item.VideoPath;
            mainWindow.AnalysisViewModel.SetResult(item.Result);
            mainWindow.NavigateToAnalysis();
        }
    }
}
