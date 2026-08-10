const LEAGUE_TEAMS = {
  mlb: [
    {abbr:"ARI",name:"Diamondbacks"},{abbr:"ATL",name:"Braves"},{abbr:"BAL",name:"Orioles"},
    {abbr:"BOS",name:"Red Sox"},{abbr:"CHC",name:"Cubs"},{abbr:"CHW",name:"White Sox"},
    {abbr:"CIN",name:"Reds"},{abbr:"CLE",name:"Guardians"},{abbr:"COL",name:"Rockies"},
    {abbr:"DET",name:"Tigers"},{abbr:"HOU",name:"Astros"},{abbr:"KC",name:"Royals"},
    {abbr:"LAA",name:"Angels"},{abbr:"LAD",name:"Dodgers"},{abbr:"MIA",name:"Marlins"},
    {abbr:"MIL",name:"Brewers"},{abbr:"MIN",name:"Twins"},{abbr:"NYM",name:"Mets"},
    {abbr:"NYY",name:"Yankees"},{abbr:"ATH",name:"Athletics"},{abbr:"PHI",name:"Phillies"},
    {abbr:"PIT",name:"Pirates"},{abbr:"SD",name:"Padres"},{abbr:"SEA",name:"Mariners"},
    {abbr:"SF",name:"Giants"},{abbr:"STL",name:"Cardinals"},{abbr:"TB",name:"Rays"},
    {abbr:"TEX",name:"Rangers"},{abbr:"TOR",name:"Blue Jays"},{abbr:"WSH",name:"Nationals"},
  ],
  nfl: [
    {abbr:"ARI",name:"Cardinals"},{abbr:"ATL",name:"Falcons"},{abbr:"BAL",name:"Ravens"},
    {abbr:"BUF",name:"Bills"},{abbr:"CAR",name:"Panthers"},{abbr:"CHI",name:"Bears"},
    {abbr:"CIN",name:"Bengals"},{abbr:"CLE",name:"Browns"},{abbr:"DAL",name:"Cowboys"},
    {abbr:"DEN",name:"Broncos"},{abbr:"DET",name:"Lions"},{abbr:"GB",name:"Packers"},
    {abbr:"HOU",name:"Texans"},{abbr:"IND",name:"Colts"},{abbr:"JAX",name:"Jaguars"},
    {abbr:"KC",name:"Chiefs"},{abbr:"LAC",name:"Chargers"},{abbr:"LAR",name:"Rams"},
    {abbr:"LV",name:"Raiders"},{abbr:"MIA",name:"Dolphins"},{abbr:"MIN",name:"Vikings"},
    {abbr:"NE",name:"Patriots"},{abbr:"NO",name:"Saints"},{abbr:"NYG",name:"Giants"},
    {abbr:"NYJ",name:"Jets"},{abbr:"PHI",name:"Eagles"},{abbr:"PIT",name:"Steelers"},
    {abbr:"SEA",name:"Seahawks"},{abbr:"SF",name:"49ers"},{abbr:"TB",name:"Buccaneers"},
    {abbr:"TEN",name:"Titans"},{abbr:"WSH",name:"Commanders"},
  ],
  nba: [
    {abbr:"ATL",name:"Hawks"},{abbr:"BOS",name:"Celtics"},{abbr:"BKN",name:"Nets"},
    {abbr:"CHA",name:"Hornets"},{abbr:"CHI",name:"Bulls"},{abbr:"CLE",name:"Cavaliers"},
    {abbr:"DAL",name:"Mavericks"},{abbr:"DEN",name:"Nuggets"},{abbr:"DET",name:"Pistons"},
    {abbr:"GS",name:"Warriors"},{abbr:"HOU",name:"Rockets"},{abbr:"IND",name:"Pacers"},
    {abbr:"LAC",name:"Clippers"},{abbr:"LAL",name:"Lakers"},{abbr:"MEM",name:"Grizzlies"},
    {abbr:"MIA",name:"Heat"},{abbr:"MIL",name:"Bucks"},{abbr:"MIN",name:"Timberwolves"},
    {abbr:"NO",name:"Pelicans"},{abbr:"NY",name:"Knicks"},{abbr:"OKC",name:"Thunder"},
    {abbr:"ORL",name:"Magic"},{abbr:"PHI",name:"76ers"},{abbr:"PHX",name:"Suns"},
    {abbr:"POR",name:"Trail Blazers"},{abbr:"SA",name:"Spurs"},{abbr:"SAC",name:"Kings"},
    {abbr:"TOR",name:"Raptors"},{abbr:"UTAH",name:"Jazz"},{abbr:"WSH",name:"Wizards"},
  ],
  nhl: [
    {abbr:"ANA",name:"Ducks"},{abbr:"BOS",name:"Bruins"},{abbr:"BUF",name:"Sabres"},
    {abbr:"CGY",name:"Flames"},{abbr:"CAR",name:"Hurricanes"},{abbr:"CHI",name:"Blackhawks"},
    {abbr:"COL",name:"Avalanche"},{abbr:"CBJ",name:"Blue Jackets"},{abbr:"DAL",name:"Stars"},
    {abbr:"DET",name:"Red Wings"},{abbr:"EDM",name:"Oilers"},{abbr:"FLA",name:"Panthers"},
    {abbr:"LA",name:"Kings"},{abbr:"MIN",name:"Wild"},{abbr:"MTL",name:"Canadiens"},
    {abbr:"NSH",name:"Predators"},{abbr:"NJ",name:"Devils"},{abbr:"NYI",name:"Islanders"},
    {abbr:"NYR",name:"Rangers"},{abbr:"OTT",name:"Senators"},{abbr:"PHI",name:"Flyers"},
    {abbr:"PIT",name:"Penguins"},{abbr:"SJ",name:"Sharks"},{abbr:"SEA",name:"Kraken"},
    {abbr:"STL",name:"Blues"},{abbr:"TB",name:"Lightning"},{abbr:"TOR",name:"Maple Leafs"},
    {abbr:"UTAH",name:"Mammoth"},{abbr:"VAN",name:"Canucks"},{abbr:"VGK",name:"Golden Knights"},
    {abbr:"WSH",name:"Capitals"},{abbr:"WPG",name:"Jets"},
  ],
  wnba: [
    {abbr:"ATL",name:"Dream"},{abbr:"CHI",name:"Sky"},{abbr:"CON",name:"Sun"},
    {abbr:"DAL",name:"Wings"},{abbr:"GS",name:"Valkyries"},{abbr:"IND",name:"Fever"},
    {abbr:"LA",name:"Sparks"},{abbr:"LV",name:"Aces"},{abbr:"MIN",name:"Lynx"},
    {abbr:"NY",name:"Liberty"},{abbr:"PHX",name:"Mercury"},{abbr:"POR",name:"Fire"},
    {abbr:"SEA",name:"Storm"},{abbr:"TOR",name:"Tempo"},{abbr:"WSH",name:"Mystics"},
  ],
  nwsl: [
    {abbr:"LA",name:"Angel City FC"},{abbr:"BAY",name:"Bay FC"},
    {abbr:"BOS",name:"Boston Legacy FC"},{abbr:"CHI",name:"Chicago Stars FC"},
    {abbr:"DEN",name:"Denver Summit FC"},{abbr:"GFC",name:"Gotham FC"},
    {abbr:"HOU",name:"Houston Dash"},{abbr:"KC",name:"Kansas City Current"},
    {abbr:"NC",name:"North Carolina Courage"},{abbr:"ORL",name:"Orlando Pride"},
    {abbr:"POR",name:"Portland Thorns FC"},{abbr:"LOU",name:"Racing Louisville FC"},
    {abbr:"SD",name:"San Diego Wave FC"},{abbr:"SEA",name:"Seattle Reign FC"},
    {abbr:"UTA",name:"Utah Royals"},{abbr:"WAS",name:"Washington Spirit"},
  ],
  mls: [
    {abbr:"ATL",name:"Atlanta United"},{abbr:"ATX",name:"Austin FC"},{abbr:"CHI",name:"Fire"},
    {abbr:"CIN",name:"FC Cincinnati"},{abbr:"CLB",name:"Crew"},{abbr:"CLT",name:"Charlotte FC"},
    {abbr:"COL",name:"Rapids"},{abbr:"DAL",name:"FC Dallas"},{abbr:"DC",name:"D.C. United"},
    {abbr:"HOU",name:"Dynamo"},{abbr:"LA",name:"Galaxy"},{abbr:"LAFC",name:"LAFC"},
    {abbr:"MIA",name:"Inter Miami"},{abbr:"MIN",name:"Loons"},{abbr:"MTL",name:"CF Montréal"},
    {abbr:"NE",name:"Revolution"},{abbr:"NSH",name:"Nashville SC"},{abbr:"NYC",name:"NYCFC"},
    {abbr:"ORL",name:"Orlando City"},{abbr:"PHI",name:"Union"},{abbr:"POR",name:"Timbers"},
    {abbr:"RBNY",name:"Red Bulls"},{abbr:"RSL",name:"Real Salt Lake"},{abbr:"SD",name:"San Diego FC"},
    {abbr:"SEA",name:"Sounders"},{abbr:"SJ",name:"Earthquakes"},{abbr:"SKC",name:"Sporting KC"},
    {abbr:"STL",name:"City SC"},{abbr:"TOR",name:"Toronto FC"},{abbr:"VAN",name:"Whitecaps"},
  ],
  premier_league: [
    {abbr:"ARS",name:"Arsenal"},{abbr:"AVL",name:"Aston Villa"},{abbr:"BOU",name:"Bournemouth"},
    {abbr:"BRE",name:"Brentford"},{abbr:"BHA",name:"Brighton"},{abbr:"CHE",name:"Chelsea"},
    {abbr:"COV",name:"Coventry"},{abbr:"CRY",name:"Crystal Palace"},{abbr:"EVE",name:"Everton"},
    {abbr:"FUL",name:"Fulham"},{abbr:"HUL",name:"Hull City"},{abbr:"IPS",name:"Ipswich"},
    {abbr:"LEE",name:"Leeds"},{abbr:"LIV",name:"Liverpool"},{abbr:"MNC",name:"Man City"},
    {abbr:"MAN",name:"Man United"},{abbr:"NEW",name:"Newcastle"},{abbr:"NFO",name:"Nottm Forest"},
    {abbr:"SUN",name:"Sunderland"},{abbr:"TOT",name:"Spurs"},
  ],
};

document.addEventListener('DOMContentLoaded', function () {
  Object.keys(LEAGUE_TEAMS).forEach(function (league) {
    const input = document.querySelector('input[name="' + league + '"]');
    if (input) setupAutocomplete(input, LEAGUE_TEAMS[league]);
  });
});

function setupAutocomplete(input, teams) {
  const dropdown = document.createElement('ul');
  dropdown.className = 'list-group position-absolute w-100 shadow-sm';
  dropdown.style.cssText = 'z-index:1000;max-height:200px;overflow-y:auto;display:none;';

  const wrapper = document.createElement('div');
  wrapper.className = 'position-relative';
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);
  wrapper.appendChild(dropdown);

  input.addEventListener('input', function () {
    const val = this.value;
    const lastComma = val.lastIndexOf(',');
    const token = (lastComma >= 0 ? val.slice(lastComma + 1) : val).trim().toLowerCase();

    if (!token) { dropdown.style.display = 'none'; return; }

    const matches = teams.filter(function (t) {
      return t.abbr.toLowerCase().startsWith(token) ||
             t.name.toLowerCase().startsWith(token);
    }).slice(0, 8);

    if (!matches.length) { dropdown.style.display = 'none'; return; }

    dropdown.innerHTML = '';
    matches.forEach(function (t) {
      const li = document.createElement('li');
      li.className = 'list-group-item list-group-item-action py-1 small';
      li.style.cursor = 'pointer';
      li.textContent = t.abbr + ' — ' + t.name;
      li.addEventListener('mousedown', function (e) {
        e.preventDefault();
        const prefix = lastComma >= 0 ? val.slice(0, lastComma + 1) + ' ' : '';
        input.value = prefix + t.abbr;
        dropdown.style.display = 'none';
        input.focus();
      });
      dropdown.appendChild(li);
    });
    dropdown.style.display = 'block';
  });

  input.addEventListener('blur', function () {
    setTimeout(function () { dropdown.style.display = 'none'; }, 150);
  });
}
