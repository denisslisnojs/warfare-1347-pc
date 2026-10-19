using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using Newtonsoft.Json.Serialization;

namespace Warfare.Core
{
    public static class DataJson
    {
        public static readonly JsonSerializerSettings Settings = new JsonSerializerSettings
        {
            ContractResolver = new DefaultContractResolver { NamingStrategy = new CamelCaseNamingStrategy() },
            Converters = { new StringEnumConverter(new CamelCaseNamingStrategy()) },
            MissingMemberHandling = MissingMemberHandling.Ignore,
            NullValueHandling = NullValueHandling.Ignore,
        };

        public static T Read<T>(string json) => JsonConvert.DeserializeObject<T>(json, Settings);

        public static string Write<T>(T value) => JsonConvert.SerializeObject(value, Formatting.Indented, Settings);
    }
}
