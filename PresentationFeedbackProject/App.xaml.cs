using System.Windows;
using PresentationFeedbackUI.Database;

namespace PresentationFeedbackUI
{
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            DbManager.InitializeDatabase();
            base.OnStartup(e);
        }
    }
}