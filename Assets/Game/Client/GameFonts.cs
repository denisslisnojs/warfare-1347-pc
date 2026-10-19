using UnityEngine;

namespace Warfare.Client
{
    public static class GameFonts
    {
        static Font text, heading, button;

        static Font Load(string name)
        {
            var f = Resources.Load<Font>("Fonts/" + name);
            return f != null ? f : Font.CreateDynamicFontFromOSFont(new[] { "Georgia", "Palatino Linotype", "Cambria" }, 32);
        }

        public static Font Text => text != null ? text : text = Load("Alegreya");
        public static Font Heading => heading != null ? heading : heading = Load("AlegreyaSC-Bold");
        public static Font Button => button != null ? button : button = Load("AlegreyaSC-Regular");
    }
}
