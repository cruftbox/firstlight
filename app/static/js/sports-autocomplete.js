const LEAGUE_TEAMS = {
  mlb: [
    {id:"3",abbr:"LAA",name:"Angels"},
    {id:"18",abbr:"HOU",name:"Astros"},
    {id:"11",abbr:"ATH",name:"Athletics"},
    {id:"14",abbr:"TOR",name:"Blue Jays"},
    {id:"15",abbr:"ATL",name:"Braves"},
    {id:"8",abbr:"MIL",name:"Brewers"},
    {id:"24",abbr:"STL",name:"Cardinals"},
    {id:"16",abbr:"CHC",name:"Cubs"},
    {id:"29",abbr:"ARI",name:"Diamondbacks"},
    {id:"19",abbr:"LAD",name:"Dodgers"},
    {id:"26",abbr:"SF",name:"Giants"},
    {id:"5",abbr:"CLE",name:"Guardians"},
    {id:"12",abbr:"SEA",name:"Mariners"},
    {id:"28",abbr:"MIA",name:"Marlins"},
    {id:"21",abbr:"NYM",name:"Mets"},
    {id:"20",abbr:"WSH",name:"Nationals"},
    {id:"1",abbr:"BAL",name:"Orioles"},
    {id:"25",abbr:"SD",name:"Padres"},
    {id:"22",abbr:"PHI",name:"Phillies"},
    {id:"23",abbr:"PIT",name:"Pirates"},
    {id:"13",abbr:"TEX",name:"Rangers"},
    {id:"30",abbr:"TB",name:"Rays"},
    {id:"2",abbr:"BOS",name:"Red Sox"},
    {id:"17",abbr:"CIN",name:"Reds"},
    {id:"27",abbr:"COL",name:"Rockies"},
    {id:"7",abbr:"KC",name:"Royals"},
    {id:"6",abbr:"DET",name:"Tigers"},
    {id:"9",abbr:"MIN",name:"Twins"},
    {id:"4",abbr:"CHW",name:"White Sox"},
    {id:"10",abbr:"NYY",name:"Yankees"},
  ],
  nfl: [
    {id:"25",abbr:"SF",name:"49ers"},
    {id:"3",abbr:"CHI",name:"Bears"},
    {id:"4",abbr:"CIN",name:"Bengals"},
    {id:"2",abbr:"BUF",name:"Bills"},
    {id:"7",abbr:"DEN",name:"Broncos"},
    {id:"5",abbr:"CLE",name:"Browns"},
    {id:"27",abbr:"TB",name:"Buccaneers"},
    {id:"22",abbr:"ARI",name:"Cardinals"},
    {id:"24",abbr:"LAC",name:"Chargers"},
    {id:"12",abbr:"KC",name:"Chiefs"},
    {id:"11",abbr:"IND",name:"Colts"},
    {id:"28",abbr:"WSH",name:"Commanders"},
    {id:"6",abbr:"DAL",name:"Cowboys"},
    {id:"15",abbr:"MIA",name:"Dolphins"},
    {id:"21",abbr:"PHI",name:"Eagles"},
    {id:"1",abbr:"ATL",name:"Falcons"},
    {id:"19",abbr:"NYG",name:"Giants"},
    {id:"30",abbr:"JAX",name:"Jaguars"},
    {id:"20",abbr:"NYJ",name:"Jets"},
    {id:"8",abbr:"DET",name:"Lions"},
    {id:"9",abbr:"GB",name:"Packers"},
    {id:"29",abbr:"CAR",name:"Panthers"},
    {id:"17",abbr:"NE",name:"Patriots"},
    {id:"13",abbr:"LV",name:"Raiders"},
    {id:"14",abbr:"LAR",name:"Rams"},
    {id:"33",abbr:"BAL",name:"Ravens"},
    {id:"18",abbr:"NO",name:"Saints"},
    {id:"26",abbr:"SEA",name:"Seahawks"},
    {id:"23",abbr:"PIT",name:"Steelers"},
    {id:"34",abbr:"HOU",name:"Texans"},
    {id:"10",abbr:"TEN",name:"Titans"},
    {id:"16",abbr:"MIN",name:"Vikings"},
  ],
  nba: [
    {id:"20",abbr:"PHI",name:"76ers"},
    {id:"15",abbr:"MIL",name:"Bucks"},
    {id:"4",abbr:"CHI",name:"Bulls"},
    {id:"5",abbr:"CLE",name:"Cavaliers"},
    {id:"2",abbr:"BOS",name:"Celtics"},
    {id:"12",abbr:"LAC",name:"Clippers"},
    {id:"29",abbr:"MEM",name:"Grizzlies"},
    {id:"1",abbr:"ATL",name:"Hawks"},
    {id:"14",abbr:"MIA",name:"Heat"},
    {id:"30",abbr:"CHA",name:"Hornets"},
    {id:"26",abbr:"UTAH",name:"Jazz"},
    {id:"23",abbr:"SAC",name:"Kings"},
    {id:"18",abbr:"NY",name:"Knicks"},
    {id:"13",abbr:"LAL",name:"Lakers"},
    {id:"19",abbr:"ORL",name:"Magic"},
    {id:"6",abbr:"DAL",name:"Mavericks"},
    {id:"17",abbr:"BKN",name:"Nets"},
    {id:"7",abbr:"DEN",name:"Nuggets"},
    {id:"11",abbr:"IND",name:"Pacers"},
    {id:"3",abbr:"NO",name:"Pelicans"},
    {id:"8",abbr:"DET",name:"Pistons"},
    {id:"28",abbr:"TOR",name:"Raptors"},
    {id:"10",abbr:"HOU",name:"Rockets"},
    {id:"24",abbr:"SA",name:"Spurs"},
    {id:"21",abbr:"PHX",name:"Suns"},
    {id:"25",abbr:"OKC",name:"Thunder"},
    {id:"16",abbr:"MIN",name:"Timberwolves"},
    {id:"22",abbr:"POR",name:"Trail Blazers"},
    {id:"9",abbr:"GS",name:"Warriors"},
    {id:"27",abbr:"WSH",name:"Wizards"},
  ],
  nhl: [
    {id:"17",abbr:"COL",name:"Avalanche"},
    {id:"4",abbr:"CHI",name:"Blackhawks"},
    {id:"29",abbr:"CBJ",name:"Blue Jackets"},
    {id:"19",abbr:"STL",name:"Blues"},
    {id:"1",abbr:"BOS",name:"Bruins"},
    {id:"10",abbr:"MTL",name:"Canadiens"},
    {id:"22",abbr:"VAN",name:"Canucks"},
    {id:"23",abbr:"WSH",name:"Capitals"},
    {id:"11",abbr:"NJ",name:"Devils"},
    {id:"25",abbr:"ANA",name:"Ducks"},
    {id:"3",abbr:"CGY",name:"Flames"},
    {id:"15",abbr:"PHI",name:"Flyers"},
    {id:"37",abbr:"VGK",name:"Golden Knights"},
    {id:"7",abbr:"CAR",name:"Hurricanes"},
    {id:"12",abbr:"NYI",name:"Islanders"},
    {id:"28",abbr:"WPG",name:"Jets"},
    {id:"8",abbr:"LA",name:"Kings"},
    {id:"124292",abbr:"SEA",name:"Kraken"},
    {id:"20",abbr:"TB",name:"Lightning"},
    {id:"129764",abbr:"UTAH",name:"Mammoth"},
    {id:"21",abbr:"TOR",name:"Maple Leafs"},
    {id:"6",abbr:"EDM",name:"Oilers"},
    {id:"26",abbr:"FLA",name:"Panthers"},
    {id:"16",abbr:"PIT",name:"Penguins"},
    {id:"27",abbr:"NSH",name:"Predators"},
    {id:"13",abbr:"NYR",name:"Rangers"},
    {id:"5",abbr:"DET",name:"Red Wings"},
    {id:"2",abbr:"BUF",name:"Sabres"},
    {id:"14",abbr:"OTT",name:"Senators"},
    {id:"18",abbr:"SJ",name:"Sharks"},
    {id:"9",abbr:"DAL",name:"Stars"},
    {id:"30",abbr:"MIN",name:"Wild"},
  ],
  wnba: [
    {id:"17",abbr:"LV",name:"Aces"},
    {id:"20",abbr:"ATL",name:"Dream"},
    {id:"5",abbr:"IND",name:"Fever"},
    {id:"132052",abbr:"POR",name:"Fire"},
    {id:"9",abbr:"NY",name:"Liberty"},
    {id:"8",abbr:"MIN",name:"Lynx"},
    {id:"11",abbr:"PHX",name:"Mercury"},
    {id:"16",abbr:"WSH",name:"Mystics"},
    {id:"19",abbr:"CHI",name:"Sky"},
    {id:"6",abbr:"LA",name:"Sparks"},
    {id:"14",abbr:"SEA",name:"Storm"},
    {id:"18",abbr:"CON",name:"Sun"},
    {id:"131935",abbr:"TOR",name:"Tempo"},
    {id:"129689",abbr:"GS",name:"Valkyries"},
    {id:"3",abbr:"DAL",name:"Wings"},
  ],
  nwsl: [
    {id:"21422",abbr:"LA",name:"Angel City"},
    {id:"22187",abbr:"BAY",name:"Bay"},
    {id:"131562",abbr:"BOS",name:"Boston"},
    {id:"15360",abbr:"CHI",name:"Chicago"},
    {id:"131563",abbr:"DEN",name:"Denver"},
    {id:"15364",abbr:"GFC",name:"Gotham"},
    {id:"17346",abbr:"HOU",name:"Houston"},
    {id:"20907",abbr:"KC",name:"Kansas City"},
    {id:"20905",abbr:"LOU",name:"Louisville"},
    {id:"15366",abbr:"NC",name:"North Carolina"},
    {id:"18206",abbr:"ORL",name:"Orlando"},
    {id:"15362",abbr:"POR",name:"Portland"},
    {id:"21423",abbr:"SD",name:"San Diego"},
    {id:"15363",abbr:"SEA",name:"Seattle"},
    {id:"19141",abbr:"UTA",name:"Utah"},
    {id:"15365",abbr:"WAS",name:"Washington"},
  ],
  mls: [
    {id:"18418",abbr:"ATL",name:"Atlanta"},
    {id:"20906",abbr:"ATX",name:"Austin"},
    {id:"9720",abbr:"MTL",name:"CF Montréal"},
    {id:"21300",abbr:"CLT",name:"Charlotte"},
    {id:"182",abbr:"CHI",name:"Chicago"},
    {id:"18267",abbr:"CIN",name:"Cincinnati"},
    {id:"184",abbr:"COL",name:"Colorado"},
    {id:"183",abbr:"CLB",name:"Columbus"},
    {id:"193",abbr:"DC",name:"D.C. United"},
    {id:"185",abbr:"DAL",name:"Dallas"},
    {id:"6077",abbr:"HOU",name:"Houston"},
    {id:"186",abbr:"SKC",name:"Kansas City"},
    {id:"187",abbr:"LA",name:"LA Galaxy"},
    {id:"18966",abbr:"LAFC",name:"LAFC"},
    {id:"20232",abbr:"MIA",name:"Miami"},
    {id:"17362",abbr:"MIN",name:"Minnesota"},
    {id:"18986",abbr:"NSH",name:"Nashville"},
    {id:"189",abbr:"NE",name:"New England"},
    {id:"17606",abbr:"NYC",name:"NYCFC"},
    {id:"12011",abbr:"ORL",name:"Orlando"},
    {id:"10739",abbr:"PHI",name:"Philadelphia"},
    {id:"9723",abbr:"POR",name:"Portland"},
    {id:"190",abbr:"RBNY",name:"Red Bull NY"},
    {id:"4771",abbr:"RSL",name:"Salt Lake"},
    {id:"22529",abbr:"SD",name:"San Diego"},
    {id:"191",abbr:"SJ",name:"San Jose"},
    {id:"9726",abbr:"SEA",name:"Seattle"},
    {id:"21812",abbr:"STL",name:"St. Louis"},
    {id:"7318",abbr:"TOR",name:"Toronto"},
    {id:"9727",abbr:"VAN",name:"Vancouver"},
  ],
  premier_league: [
    {id:"359",abbr:"ARS",name:"Arsenal"},
    {id:"362",abbr:"AVL",name:"Aston Villa"},
    {id:"349",abbr:"BOU",name:"Bournemouth"},
    {id:"337",abbr:"BRE",name:"Brentford"},
    {id:"331",abbr:"BHA",name:"Brighton"},
    {id:"384",abbr:"CRY",name:"C Palace"},
    {id:"363",abbr:"CHE",name:"Chelsea"},
    {id:"388",abbr:"COV",name:"Coventry"},
    {id:"368",abbr:"EVE",name:"Everton"},
    {id:"370",abbr:"FUL",name:"Fulham"},
    {id:"306",abbr:"HUL",name:"Hull"},
    {id:"373",abbr:"IPS",name:"Ipswich"},
    {id:"357",abbr:"LEE",name:"Leeds"},
    {id:"364",abbr:"LIV",name:"Liverpool"},
    {id:"382",abbr:"MNC",name:"Man City"},
    {id:"360",abbr:"MAN",name:"Man United"},
    {id:"361",abbr:"NEW",name:"Newcastle"},
    {id:"393",abbr:"NFO",name:"Nottm Forest"},
    {id:"367",abbr:"TOT",name:"Spurs"},
    {id:"366",abbr:"SUN",name:"Sunderland"},
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

    // Substring rather than prefix: "city" should find Man City, and once the
    // field holds ids the user has no other way to search.
    const matches = teams.filter(function (t) {
      return t.abbr.toLowerCase().includes(token) ||
             t.name.toLowerCase().includes(token);
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
        // Write the ESPN team id, not the abbreviation. Abbreviations are
        // display labels ESPN revises (ACFC -> LA), and a stale one silently
        // matches nothing. The id never changes.
        const prefix = lastComma >= 0 ? val.slice(0, lastComma + 1) + ' ' : '';
        input.value = prefix + t.id;
        dropdown.style.display = 'none';
        input.focus();
        describe();
      });
      dropdown.appendChild(li);
    });
    dropdown.style.display = 'block';
  });

  input.addEventListener('blur', function () {
    setTimeout(function () { dropdown.style.display = 'none'; }, 150);
  });

  // The field stores ids, which are unreadable on their own. Echo the team
  // names underneath so the saved value is still verifiable at a glance, and
  // so an entry that resolves to nothing is visible rather than silent.
  const hint = document.createElement('div');
  hint.className = 'form-text small';
  wrapper.parentNode.insertBefore(hint, wrapper.nextSibling);

  function describe() {
    const entries = input.value.split(',').map(s => s.trim()).filter(Boolean);
    if (!entries.length) { hint.textContent = ''; return; }
    const labels = entries.map(function (entry) {
      const key = entry.toLowerCase();
      const hit = teams.find(t => t.id === entry ||
                                  t.abbr.toLowerCase() === key ||
                                  t.name.toLowerCase() === key);
      return hit ? hit.name : entry + ' (unrecognized)';
    });
    hint.textContent = labels.join(', ');
  }

  input.addEventListener('input', describe);
  describe();
}
